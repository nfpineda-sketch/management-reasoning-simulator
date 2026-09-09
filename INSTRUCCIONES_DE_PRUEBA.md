# Prueba guiada — v0.8.21

## Preparación

1. Abre `http://localhost:8501`.
2. Pulsa `Reset scenario` si existe una trayectoria anterior.
3. Confirma el encabezado `MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry`.
4. En PS001, confirma que el monitor y la presentación inicial muestran `90/54 · MAP 66`.

## Regresión visual: ECG dinámico

1. Abre `Patient Data → ECG` al iniciar PS001.
2. Confirma que se vea una tira de DII sobre papel milimetrado, con complejos QRS angostos, intervalos R–R irregulares y actividad fibrilatoria, rotulada `25 mm/s · 10 mm/mV`.
3. Confirma que la interpretación indique fibrilación auricular con respuesta ventricular rápida cercana a 162/min.
4. Administra una intervención de control de frecuencia y confirma que el trazado continúe irregular si la FA persiste, pero que la separación entre los QRS aumente al bajar la frecuencia.
5. Realiza una cardioversión sincronizada exitosa y confirma que el trazado cambie a ritmo regular con una onda P antes de cada QRS.
6. Comprueba que debajo del trazado aparezca `Synthetic educational rhythm strip · Lead II`.

## Regresión principal: revisión de las Decisiones 2, 7 y 8

Completa una trayectoria que incluya cardioversión con sedación, un bolo inicial de 500 mL, POCUS, laboratorios/lactato, uroanálisis/radiografía, reevaluación, un bolo tardío de 2000 mL y finalmente norepinefrina con ceftriaxona. En la revisión selecciona las Decisiones 2, 7 y 8.

Confirma que:

- existan tres comparaciones expertas, una para cada decisión seleccionada;
- la comparación de la Decisión 2 describa el bolo de 500 mL y el estado poscardioversión;
- la comparación de la Decisión 7 describa los 2000 mL en el estado real de shock y no proponga cardioversión basándose solo en el número 7;
- la comparación de la Decisión 8 describa norepinefrina y ceftriaxona;
- el cue y el threshold del Adaptation Plan contengan condiciones observables como MAP, relleno capilar, estado mental o lactato, sin duplicar una instrucción de titular norepinefrina;
- el PDF contenga Management Trace, las tres Decision Reviews, las tres Expert Comparisons y el Prospective Adaptation Plan con espaciado normal.

Las entradas exactas de esta trayectoria están incluidas más adelante en este documento.

## Regresión dirigida: bolo de 2000 mL con reevaluación a 5 minutos

Reproduce la trayectoria de cardioversión, 500 mL, POCUS, laboratorio/lactato, uroanálisis/radiografía y una espera de 10 minutos. Cuando el reloj llegue aproximadamente a `00:50` y el paciente esté nuevamente en shock, envía:

```text
Patient hypotensive with slow perfusion and neurologic dysfunction; urianalysis positive for infection. Give 2000 cc NS. I want to improve arterial pressure and tissue perfusion. I expect pressure to increase and perfusion to improve. Reassess perfusion, HR, and BP in 5 minutes.
```

Confirma que:

- el reloj avance exactamente 5 minutos, por ejemplo de `00:50` a `00:55`, y no 18 minutos;
- se registren exactamente `2000 mL Normal saline`;
- exista una respuesta temprana modesta de presión/perfusión, sin una normalización artificial del shock;
- no aparezca el colapso terminal `60/28 · MAP 39` causado por el salto temporal anterior;
- el cuadro todavía permita y haga clínicamente pertinente continuar con antibióticos y soporte vasoactivo.

Si en el mismo turno solicitas un estudio cuyo resultado tarda 10 minutos y una reevaluación a 5 minutos, el reloj debe respetar los 10 minutos necesarios para entregar ese resultado.

## Regresión dirigida: modelo poscardioversión y efecto esperado separados

Después de la cardioversión, con ritmo sinusal, envía literalmente:

```text
Although the rhythm is now sinus, reduced effective circulating volume may still be contributing to incomplete perfusion recovery. Give 500 mL normal saline IV. I want to improve preload and tissue perfusion. I expect improved blood pressure, capillary refill, and extremity temperature without worsening oxygenation or work of breathing. Reassess HR and rhythm, BP/MAP, capillary refill, extremities, mental status, SpO2, and work of breathing in 10 minutes.
```

La orden debe ejecutarse directamente, sin `ORDER HELD`. Confirma que:

- `Working model` contenga la apreciación iniciada con `Although...`;
- `Management priority` sea `improve preload and tissue perfusion`;
- `Expected effect` comience con `improved blood pressure` y no duplique la prioridad;
- se administren exactamente `500 mL` de solución salina;
- la reevaluación ocurra a los 10 minutos.

## Regresión dirigida: interpretación flexible y solo pedir lo ausente

1. Selecciona `PS001 · Tachyarrhythmia in an Acutely Ill Patient` y pulsa `Begin Encounter`.
2. Envía literalmente:

```text
Patient hypotensive, slow perfusion, tachycardia, neurologic dysfunction. urianalysis positive for infection. give 2000 cc NS, reassess perfusion, hr, bp. I expect pressure to increase, decrease hr and improving perfusion
```

3. La orden debe quedar retenida únicamente porque falta el tiempo de reevaluación.
4. Los recuadros deben aparecer prellenados con el modelo clínico, la prioridad `improve arterial pressure and tissue perfusion`, el efecto esperado y las variables `perfusion, hr, bp`.
5. Si el estado actual muestra HR 96/min, puede aparecer un aviso neutral indicando que el texto menciona taquicardia. Ese aviso no debe calificarse como contradicción ni impedir avanzar.
6. Completa el tiempo con `5` minutos y confirma que se administren exactamente `2000 mL` de solución salina.
7. Repite la prueba agregando `in 5 minutes` al final de la entrada original. La orden debe ejecutarse directamente, sin aclaración.
8. Pulsa `Reset scenario` antes de la prueba siguiente.

## Regresión dirigida: sedación procedural ejecutable y secuencia transparente

1. Selecciona `PS001 · Tachyarrhythmia in an Acutely Ill Patient` y pulsa `Begin Encounter`.
2. Completa la primera decisión hasta obtener una respuesta con FA persistente y luego envía literalmente:

```text
Still in afib, i want to do rythm management. Cardiovert sincronized 200 j. Sedation with etomidate 8 mg + midazolam 2 mg. Reassess in 10 minutes, rhythm, hr, bp and perfusion
```

3. Debe aparecer `ORDER HELD — REASONING REQUIRED` sin modificar la hora ni los signos vitales.
4. Deben estar marcados como presentes `Working model`, `Management priority`, `Reassessment variables` y `Reassessment timing`.
5. Solo `Expected effect` debe permanecer ausente.
6. La orden retenida debe mostrar `procedural sedation with etomidate 8 mg IV + midazolam 2 mg IV` antes de `synchronized cardioversion 200 J`. Como todavía falta el efecto esperado, ninguna de las tres acciones debe haberse ejecutado.
7. Completa únicamente `I expect…` con:

```text
conversion to sinus rhythm with improved perfusion
```

8. Debe aparecer una sola respuesta integrada que indique primero `procedural sedation with etomidate 8 mg IV + midazolam 2 mg IV` y luego `synchronized cardioversion 200 J`.
9. En `Treatments` deben aparecer etomidato 8 mg y midazolam 2 mg como administrados; la cardioversión debe haberse ejecutado una sola vez.
10. El estado mental inmediato o temprano puede mostrarse como `Sedated` y luego `Drowsy` mientras se disipa el efecto; esto no debe interpretarse como deterioro neurológico por shock.
11. Pulsa `Reset scenario` antes de continuar con las pruebas restantes.

## Regresión dirigida: orden retenida hasta explicitar el razonamiento

1. Selecciona `PS001 · Tachyarrhythmia in an Acutely Ill Patient` y pulsa `Begin Encounter`.
2. Envía solamente:

```text
Give diltiazem 5 mg IV.
```

3. Debe aparecer `ORDER HELD — REASONING REQUIRED` y la orden entendida `diltiazem 5 mg IV`.
4. Confirma que la hora y los signos vitales no cambien.
5. El aviso debe indicar los cinco criterios ausentes (modelo, prioridad, efecto, variables y tiempo) y mostrar los campos guiados.
6. Sin repetir la orden, prueba primero esta respuesta natural, sin usar los nombres exactos de los campos:

```text
I.m addressing heart rate first. I think AF is contributing to poor perfusion. With diltiazem I expect a moderate decrease in heart rate. Reassess HR, perfusion, and blood pressure in 5 minutes.
```

7. La respuesta debe ser interpretada sin una nueva aclaración, la orden retenida debe ejecutarse una sola vez y el reloj debe avanzar cinco minutos.
8. Pulsa `Reset scenario` y repite los pasos 1–5. Esta vez completa directamente los espacios bajo `Complete the sentence starters`:

```text
My working model is AF with RVR impairing cardiac filling. My priority is cautious rate control while preserving perfusion. I expect this to reduce heart rate without hypotension. Reassess HR and rhythm, BP, capillary refill, and mental status in 5 minutes.
```

9. Confirma otra vez una sola ejecución y ningún cambio de estado antes de completar los campos.
10. Pulsa `Reset scenario` antes de la prueba siguiente.

## Regresión dirigida: antecedente explícito y completación limpia

1. Selecciona `PS001 · Tachyarrhythmia in an Acutely Ill Patient` y pulsa `Begin Encounter`.
2. Envía literalmente:

```text
Give patient diltiazem 5 mg IV. I'm addressing heart rate first because I think it is the primary problem. I expect a moderate decrease in heart rate, maybe better perfusion. Reassess in 10 minutes.
```

3. La orden debe quedar retenida únicamente porque faltan variables específicas de reevaluación; no debe pedir de nuevo el modelo de trabajo, la prioridad ni el efecto esperado.
4. Completa solo el campo faltante con `HR, BP, and perfusion` y envía.
5. Confirma que la cronología muestre `REASONING COMPLETION`, no una segunda entrada `YOU`.
6. La completación debe mostrar `Working model: heart rate is the primary problem`; no debe mostrar una construcción redundante con `it is`.
7. Confirma que diltiazem se administre una sola vez y que el estado del paciente no cambie antes de completar el razonamiento.
8. Pulsa `Reset scenario` antes de la prueba siguiente.

## Regresión dirigida: prioridad expresada sin frase obligatoria

1. Selecciona `PS001 · Tachyarrhythmia in an Acutely Ill Patient` y pulsa `Begin Encounter`.
2. Envía literalmente:

```text
I think patient is in shock, probably driven by the afib. I would try to control heart rate. Give diltiazem 5 mg IV. I would expect heart rate to decrease and better perfusion. Reassess HR, BP, and perfusion in 10 minutes.
```

3. La orden debe ejecutarse directamente, sin aparecer `ORDER HELD — REASONING REQUIRED`.
4. El sistema debe interpretar `control heart rate` como prioridad aunque el alumno no escriba `My priority is` ni `first`.
5. Confirma que diltiazem se administre una sola vez y que el reloj avance a `00:10`.
6. Pulsa `Reset scenario` antes de la prueba siguiente.

## Regresión dirigida: volumen IV frente a flujo de oxígeno

Antes de continuar, comprueba también esta segunda forma natural de expresar prioridad:

```text
I think patient is in shock due to afib. I want to control heart rate with diltiazem 5 mg IV. I expect decrease in heart rate and improve in clinical perfusion. Reassess HR, BP, and perfusion in 10 minutes.
```

La orden debe ejecutarse directamente. La prioridad interpretada debe ser `control heart rate`, sin incluir `with diltiazem`, y diltiazem debe administrarse una sola vez.

1. Selecciona `PS001 · Tachyarrhythmia in an Acutely Ill Patient` y pulsa `Begin Encounter`.
2. Envía literalmente:

```text
My working model is hypovolemia with impaired tissue perfusion while AF with RVR remains a possible contributor. My priority is cautious preload support and early phenotyping. Give 1000 NS iv, obtain POCUS, lactate, and VBG, and initiate O2 3lt nassal canula. I expect this to improve peripheral perfusion without worsening respiratory status. Reassess BP, HR and rhythm, capillary refill, extremities, SpO2, and work of breathing in 10 minutes.
```

3. Confirma que la respuesta indique `After 1000 mL Normal saline + Nasal cannula 3 L/min`.
4. Deben aparecer resultados de POCUS, lactato y VBG, y el tiempo simulado debe avanzar a `00:10`.
5. No debe aparecer `3000 mL` en la respuesta, Treatments ni Management Trace.
6. Pulsa `Reset scenario` antes de comenzar la trayectoria completa siguiente.

## Trayectoria completa del Caso 1

1. Selecciona `PS001 · Tachyarrhythmia in an Acutely Ill Patient` y pulsa `Begin Encounter`.
2. Envía esta entrada literal:

```text
My working model is AF with RVR and impaired peripheral perfusion, but the rhythm may be secondary to an acute illness rather than the sole cause of instability. My priority is to assess the hemodynamic phenotype and reversible causes before committing to rate control or cardioversion. Give 500 mL normal saline, obtain POCUS, lactate, VBG, basic labs, and ask about fever and urinary symptoms. I expect improved peripheral perfusion without worsening oxygenation or respiratory status. Reassess BP, HR and rhythm, capillary refill, extremities, mental status, SpO2, work of breathing, and lung findings in 5 minutes.
```

3. Confirma que no aparezca una pregunta sobre energía y que no se ejecute cardioversión.
4. Deben aparecer la historia de disuria, frecuencia urinaria, escalofríos y baja ingesta, además de POCUS, lactato, VBG y laboratorio básico.
5. El ritmo debe continuar en AF. En la trayectoria determinista validada, a los 10 minutos muestra aproximadamente BP 106/64, HR 171/min, SpO₂ 93%, CRT 4 s y estado mental alerta.
6. Continúa con las diez entradas siguientes para completar la trayectoria docente; las Entradas 2 y 3 comprueban además la continuidad de antibióticos.

### Caso 1 · Entrada 2

```text
The history, elevated inflammatory markers, lactate 4.9 mmol/L, hyperdynamic LV, and small collapsible IVC suggest urinary-source sepsis with persistent hypovolemia and impaired tissue perfusion. AF with RVR may be contributing, but it is not yet clearly the primary cause of instability. My priority is source-directed treatment and further cautious preload optimization before using an AV-nodal blocker. Obtain blood cultures and urinalysis, administer ceftriaxone 2 g IV, give an additional 500 mL of normal saline, and reassess BP, HR and rhythm, capillary refill, extremities, mental status, SpO2, work of breathing, and lung findings in 10 minutes. I expect improved peripheral perfusion and possibly a partial reduction in heart rate without pulmonary congestion.
```

Esperado aproximadamente a las `00:20`: BP `102/63`, HR `171/min` en AF, SpO₂ `93%`, CRT `4 s`, extremidades más calientes y estado mental alerta. Deben aparecer hemocultivos, urinalysis compatible con foco urinario, ceftriaxona `2 g IV` y los `500 mL` adicionales.

### Caso 1 · Entrada 3 — continuidad, no repetir antibióticos

```text
The urinary source is now supported and antibiotics have been started. After 1000 mL of cumulative fluid, MAP remains 76 mmHg and mental status is preserved, with slightly warmer extremities but persistent capillary refill of 4 seconds and AF at 171/min. My working model is sepsis-driven AF with persistent RVR that may now be contributing to impaired forward flow. My priority is a cautious diagnostic-therapeutic trial of rate control rather than immediate cardioversion. Give diltiazem 5 mg IV and reassess HR and rhythm, BP and MAP, capillary refill, extremities, mental status, SpO2, and work of breathing in 5 minutes. I expect a modest reduction in heart rate without hypotension or worsening tissue perfusion. Do not give additional AV-nodal blocker if MAP falls below 65 mmHg, mental status worsens, or capillary refill increases.
```

Esperado aproximadamente a las `00:25`:

- la respuesta debe comenzar con `After diltiazem 5 mg IV`;
- no debe incluir `broad-spectrum antibiotics` ni volver a administrar ceftriaxona;
- BP `101/63`, MAP `76`, HR `157/min` en AF, SpO₂ `93%`, CRT `4 s`, extremidades más calientes y estado mental alerta;
- no debe ejecutarse cardioversión.

### Caso 1 · Entrada 4 — segunda prueba cautelosa de control de frecuencia

```text
The heart rate decreased from 171 to 157/min after diltiazem without hypotension or worsening peripheral perfusion. This suggests that the ventricular response is partly responsive to AV-nodal blockade, although the persistent capillary refill of 4 seconds indicates that the underlying septic physiology remains active. My priority is cautious further rate control while preserving blood pressure and tissue perfusion. Give another diltiazem 5 mg IV and reassess HR and rhythm, BP and MAP, capillary refill, extremities, mental status, SpO2, and work of breathing in 5 minutes. I expect a further reduction in heart rate without a fall in MAP or worsening capillary refill.
```

Esperado aproximadamente a las `00:30`: BP `101/63`, MAP `76`, HR `138/min` en AF, SpO₂ `93%`, CRT `4 s`, extremidades más calientes y estado mental alerta.

### Caso 1 · Entrada 5 — POCUS dinámico

```text
The ventricular rate has decreased from 171 to 138/min without hypotension, but capillary refill remains 4 seconds. This suggests that rate reduction alone has not corrected the perfusion abnormality. My priority is to reassess the septic hemodynamic phenotype before giving more AV-nodal blockade. Repeat POCUS and lactate, and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, work of breathing, and lung findings in 10 minutes. I expect the heart rate to remain controlled without worsening pressure while the new data clarify whether further preload support or vasopressor therapy is needed.
```

Esperado:

- a las `00:32`, el POCUS repetido debe mostrar `moderately to severely reduced LV systolic function`, no el hallazgo hiperdinámico basal;
- debe conservar IVC de aproximadamente `1.4 cm` con `>50%` de variación respiratoria y ausencia de B-lines difusas;
- el lactato debe ser aproximadamente `5.0 mmol/L` a las `00:35`;
- a las `00:40`, BP `94/57`, MAP `69`, HR `126/min` en AF, CRT `5 s`, extremidades frías y estado mental alerta.

### Caso 1 · Entrada 6 — sostener presión sin más bloqueo nodal

```text
Despite substantial rate reduction, perfusion has worsened: MAP is 69 mmHg, capillary refill is 5 seconds, lactate is 5.0 mmol/L, and the current POCUS demonstrates moderately to severely reduced LV systolic function. My working model is evolving low-output septic shock, likely compounded by the cumulative hemodynamic effect of AV-nodal blockade, rather than instability caused primarily by the ventricular rate. My priority is to restore perfusion pressure without further rate-control medication. Start norepinephrine 0.05 mcg/kg/min and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing in 5 minutes. I expect improved blood pressure, but I will not consider the intervention successful unless peripheral perfusion and mental status also stabilize or improve.
```

Esperado aproximadamente a las `00:45`: BP `108/73`, MAP `85`, HR `126/min` en AF, CRT `5 s`, extremidades frías y estado mental somnoliento. La presión mejora, pero la perfusión clínica no.

### Caso 1 · Entrada 7 — cardioversión como prueba causal

```text
Norepinephrine restored arterial pressure, but capillary refill has not improved and the patient is now drowsy despite a MAP of 85 mmHg. Persistent clinical instability despite adequate pressure raises concern that AF and loss of effective cardiac filling may still be contributing to low forward flow, even though the ventricular rate is lower. My priority is to test the contribution of the rhythm while maintaining circulatory support. Perform synchronized cardioversion with 200 J and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing in 5 minutes. I expect conversion to sinus rhythm; clinical benefit would require improvement in capillary refill or mental status, not electrical conversion alone.
```

Esperado aproximadamente a las `00:50`: BP `112/76`, MAP `88`, HR `89/min` en ritmo sinusal, pero CRT `5 s`, extremidades frías y estado mental somnoliento. La conversión eléctrica aislada no debe presentarse como recuperación clínica.

### Caso 1 · Entrada 8 — confirmar el fenotipo posterior a la cardioversión

```text
Cardioversion restored sinus rhythm at 89/min, but capillary refill remains 5 seconds and mental status remains drowsy despite MAP 88 mmHg. This indicates that electrical conversion alone did not restore forward flow. My priority is to reassess current ventricular function and tissue perfusion before selecting further hemodynamic support. Repeat POCUS and lactate, and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing in 10 minutes. I expect the rhythm to remain sinus; persistent LV dysfunction or rising lactate would support a low-output phenotype requiring flow-directed rather than rate-directed treatment.
```

Esperado:

- POCUS a las `00:52`: `moderately to severely reduced LV systolic function`;
- lactato aproximadamente `5.6 mmol/L` a las `00:55`;
- a las `01:00`: BP `111/74`, MAP `86`, HR `89/min` en ritmo sinusal, SpO₂ `92%`, CRT `5 s`, extremidades frías y estado mental somnoliento.

La persistencia de disfunción del VI es el punto de decisión para soporte dirigido al flujo.

### Caso 1 · Entrada 9 — soporte dirigido al flujo

```text
Cardioversion restored sinus rhythm, but the current POCUS demonstrates moderately to severely reduced LV systolic function and lactate has risen to 5.6 mmol/L. My working model is persistent low-output septic shock despite adequate arterial pressure and rhythm conversion. My priority is to improve forward flow while preserving MAP and oxygenation. Start dobutamine 2.5 mcg/kg/min, continue the current norepinephrine infusion, repeat lactate in 10 minutes, and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing in 10 minutes. I expect improved capillary refill, mental status, and lactate without hypotension or recurrent tachyarrhythmia.
```

Esperado aproximadamente a las `01:10`: BP `112/72`, MAP `85`, HR `89/min` en ritmo sinusal, SpO₂ `92%`, CRT `3 s`, extremidades más calientes y estado mental somnoliento. El lactato puede subir transitoriamente a `5.8 mmol/L`; la mejoría periférica temprana no debe presentarse como recuperación completa.

### Caso 1 · Entrada 10 — distinguir respuesta temprana de recuperación completa

```text
The improvement in capillary refill from 5 to 3 seconds and warmer extremities suggests early forward-flow recruitment after dobutamine, but persistent drowsiness and lactate 5.8 mmol/L indicate incomplete recovery. My priority is to distinguish delayed metabolic and neurologic recovery from ongoing low output while avoiding premature escalation. Continue the current hemodynamic support unchanged. Repeat POCUS and lactate in 10 minutes, and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing in 10 minutes. I expect sustained peripheral perfusion, improving ventricular function and lactate, and gradual recovery of mental status without hypotension or recurrent AF.
```

Esperado aproximadamente a las `01:20`: BP `111/71`, MAP `84`, HR `89/min` en ritmo sinusal, SpO₂ `92%`, CRT `3 s`, extremidades más calientes y estado mental somnoliento. POCUS continúa mostrando disfunción sistólica cualitativa y el lactato baja aproximadamente a `4.4 mmol/L`.

### Caso 1 · Entrada 11 — consolidar la respuesta sin sobretratar

```text
The fall in lactate from 5.8 to 4.4 mmol/L together with sustained capillary refill of 3 seconds and warmer extremities indicates improving tissue perfusion despite persistent qualitative LV dysfunction. Mental recovery remains delayed. My priority is to preserve the current hemodynamic gains and reassess neurologic and metabolic recovery without escalating support solely because ventricular function remains abnormal on bedside imaging. Continue the current hemodynamic support unchanged, repeat lactate in 10 minutes, and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing in 10 minutes. I expect further lactate clearance and gradual improvement in mental status while maintaining sinus rhythm, blood pressure, and peripheral perfusion.
```

Esperado aproximadamente a las `01:30`: BP `110/71`, MAP `84`, HR `89/min` en ritmo sinusal, SpO₂ `92%`, CRT `3 s`, extremidades calientes, estado mental alerta y lactato `4.1 mmol/L`.

## Cerrar y revisar el Caso 1

1. Pulsa `Complete Encounter & Begin Review` después de la Entrada 11.
2. Confirma que el Management Trace queda congelado y selecciona exactamente:

   - Decisión 3 · `Rate control as a diagnostic–therapeutic trial`;
   - Decisión 7 · `Electrical success versus clinical benefit`;
   - Decisión 9 · `Pressure–flow–perfusion adaptation`.

3. En la Decisión 8 del Management Trace deben aparecer por separado:

   - `Problem: electrical conversion alone did not restore forward flow`;
   - `Expected effect: the rhythm to remain sinus`.

4. En la Decisión 11, `Rationale` debe terminar en `ventricular function remains abnormal on bedside imaging`. No debe contener `Continue the current...`, las órdenes, la expectativa ni el plan de reevaluación.
5. Comprueba que los encabezados se lean como `00:00 · Decision 1` y que cada cambio clínico use una línea o elemento separado con dos puntos, por ejemplo `Rhythm: AF → AF`.
6. Completa los cuatro campos de las tres decisiones. Al terminar, pulsa `Lock Decision Review & Reveal Expert Comparison`.
7. Confirma que cada una de las Decisiones 3, 7 y 9 muestra un modelo independiente con framing, priority, three key cues, action, trade-off y reassessment.
8. Completa los dos campos de comparación por decisión, termina el Adaptation Plan y abre `Final Summary`.
9. Descarga `ps001_decision_review_v0819.pdf`, `ps001_decision_review_v0819.md` y `ps001_decision_review_v0819.json`.
10. Abre el PDF y confirma que tenga encabezado y número de página, estado `Complete`, y las secciones `Management Trace`, `Decision Review`, `Expert Comparison` y `Prospective Adaptation Plan`.
11. El Markdown debe conservar títulos, metadatos y cambios clínicos en líneas legibles. Ninguna exportación debe contener `physiology`, `hidden` ni `forward_flow_state`.

Pulsa `Reset scenario` antes de iniciar la trayectoria respiratoria.

## Comprobar la visibilidad persistente

Antes de ingresar la primera orden, confirma que aparezca `Live patient state` con:

- hora clínica;
- BP/MAP;
- HR y ritmo;
- SpO₂ y soporte respiratorio;
- frecuencia respiratoria y trabajo respiratorio;
- CRT y extremidades;
- estado mental.

Desplázate hacia abajo. El monitor debe permanecer visible en la parte superior. Después de cada intervención ejecutada debe aparecer una tarjeta `PATIENT RESPONSE` con los signos vitales correspondientes a ese momento.

Al completar varias entradas, vuelve a las tarjetas anteriores: sus valores deben conservarse sin adoptar los signos vitales más recientes.

## Construir la trayectoria respiratoria

Pulsa `Reset scenario`, selecciona `PS002 · Acute Dyspnea with Shock` y pulsa `Begin Encounter`. Envía cada entrada por separado y espera la respuesta antes de continuar.

### Entrada 1

```text
My working model is shock with impaired perfusion and concurrent hypoxemic respiratory distress. My priority is initial preload support, oxygenation, and rapid hemodynamic phenotyping. Start with 1500 cc NS, oxygen nasal canula 4L, and obtain POCUS, lactate, VBG, and lab tests. I expect this to improve blood pressure, peripheral perfusion, and oxygenation. Reassess BP, capillary refill, extremities, SpO2, and work of breathing in 15 minutes.
```

### Entrada 2

```text
The blood pressure improved after fluid, but severe hypoxemia and respiratory distress persist, so shock has not been fully resolved. My working model is persistent hypoxemic respiratory failure with residual perfusion risk. My priority is to improve oxygenation and reduce work of breathing while watching perfusion. Start BiPAP 18/6 with O2 100%. I expect this to improve oxygenation and respiratory distress without worsening blood pressure or peripheral perfusion. Reassess BP, capillary refill, SpO2, and work of breathing in 10 minutes.
```

### Entrada 3

```text
The patient remains in shock despite partial fluid responsiveness, and BiPAP has worsened perfusion while hypoxemia persists. My priority is to restore perfusion pressure before intubation. Start norepinephrine 0.1 mcg/kg/min and prepare for intubation. I expect improved blood pressure and capillary refill. Reassess perfusion in 5 minutes.
```

### Entrada 4

```text
Perfusion pressure has improved, but severe hypoxemic respiratory failure persists despite BiPAP. My priority is definitive airway and oxygenation support while maintaining vasopressor support. Proceed with intubation, continue the current norepinephrine infusion, and start VC/AC ventilation with FiO2 100% and PEEP 10 cm H2O. I expect improved oxygenation without loss of perfusion pressure. Reassess oxygenation and perfusion in 10 minutes.
```

### Entrada 5 — continuidad, no segunda intubación

Repite exactamente la Entrada 4.

Debe aparecer `continued VC/AC ventilation`, sin una nueva intubación ni aclaración de norepinefrina.

### Entrada 6 — PEEP

```text
My working model is persistent recruitable hypoxemia despite invasive ventilation. My priority is to improve alveolar recruitment while monitoring the hemodynamic cost of higher intrathoracic pressure. Increase PEEP to 14 cm H2O. I expect improved oxygenation without worsening blood pressure or peripheral perfusion. Reassess oxygenation, blood pressure, and perfusion in 10 minutes.
```

### Entrada 7 — FiO₂

```text
My working model is adequate oxygenation on an unnecessarily high FiO2 after recruitment. My priority is to reduce excess oxygen exposure while preserving gas exchange. Decrease ventilator FiO2 to 60%. I expect oxygenation to remain adequate without increased work of breathing. Reassess SpO2 and oxygenation in 10 minutes.
```

La FiO₂ debe cambiar a 60%. Si no se modificó simultáneamente el PEEP o el modo, la SpO₂ no debe aparecer aumentando como consecuencia directa de reducir la FiO₂.

### Entrada 8 — ABG y lactato inmediatos

```text
Obtain an ABG and repeat lactate, then reassess oxygenation and perfusion in 10 minutes.
```

ABG y lactato deben conservar sus tiempos habituales de disponibilidad porque la frase `then reassess` inicia una cláusula temporal diferente.

En Management Trace, la Action debe mostrarse como `ABG + lactate`, respetando el orden escrito.

## Trayectoria principal preservada

### Entrada 9 — titulación y diagnóstico programado

```text
Despite adequate oxygenation, the patient has worsening shock with BP 94/53, capillary refill 7 seconds, very cold extremities, and lactate 5.5 mmol/L. My priority is to improve perfusion. Increase norepinephrine to 0.2 mcg/kg/min, continue the current ventilator settings. I expect improved blood pressure and peripheral perfusion without loss of oxygenation. Reassess blood pressure, capillary refill, extremities, oxygenation, and lactate in 10 minutes.
```

Esperado:

- norepinefrina cambia de `0.1` a `0.2 mcg/kg/min`;
- la descripción dice `norepinephrine increased from 0.1 to 0.2 mcg/kg/min`;
- Management Trace conserva el orden `norepinephrine ... + continue VC/AC ventilation ... + lactate`;
- el lactato aparece a los 10 minutos, no a los 5;
- Management Trace captura `worsening shock` como Problem;
- el Problem conserva exactamente `BP 94/53` y `lactate 5.5 mmol/L`, alineados con los datos disponibles y sin truncar el decimal;
- Reassessment target conserva `blood pressure, capillary refill, extremities, and lactate`;
- el nuevo lactato aparece también dentro de `Observed response` de esa misma decisión;
- Reflect & Compare contrasta `adequate oxygenation` con SpO₂, FiO₂ y P/F disponibles.

### Entrada 10 — mención retrospectiva

```text
The MAP changed minimally after increasing norepinephrine, while capillary refill, extremity perfusion, and lactate worsened. My working model is persistent shock with pressure-flow dissociation, possibly compounded by high intrathoracic pressure and vasoconstriction. My priority is to reassess the hemodynamic phenotype before further escalation. Repeat POCUS to reassess LV function, RV size, IVC, and lung B-lines, and reassess perfusion in 5 minutes.
```

Esperado:

- no solicita una dosis de norepinefrina;
- `after increasing norepinephrine` permanece como razonamiento retrospectivo;
- `lactate worsened` no genera un nuevo lactato;
- POCUS aparece aproximadamente a los 2 minutos;
- la actualización clínica ocurre a los 5 minutos;
- la única nueva Action diagnóstica es POCUS;
- el resultado describe `positive-pressure ventilation`, muestra `PEEP 14 cm H₂O` y advierte que la variación respiratoria no se interpreta como marcador aislado de precarga;
- el resultado de POCUS aparece dentro de `Observed response` de la Decisión 10, aunque sea la última decisión;
- Management Trace conserva el Working model y `perfusion` como Reassessment target.

### Caso 2 · Entrada 11 — adaptación posterior al POCUS

```text
The available POCUS shows preserved to hyperdynamic LV function without RV dilation or diffuse B-lines, while shock persists. My priority is to support forward flow and reduce intrathoracic-pressure burden while preserving oxygenation. Reduce PEEP to 10 cm H2O, increase norepinephrine to 0.3 mcg/kg/min, start dobutamine 2.5 mcg/kg/min, and repeat lactate in 10 minutes. I expect improved blood pressure, capillary refill, and lactate. Reassess blood pressure, capillary refill, extremities, oxygenation, and lactate in 10 minutes.
```

Esperado:

- no solicita aclaraciones;
- PEEP cambia de 14 a `10 cm H₂O`;
- norepinefrina cambia de 0.2 a `0.3 mcg/kg/min`;
- inicia dobutamina `2.5 mcg/kg/min`;
- el nuevo lactato aparece a los 10 minutos;
- Management Trace conserva el orden `adjust ventilation → norepinephrine → dobutamine → lactate`;
- `Observed response` separa visualmente `Clinical response` de `New diagnostic information`;
- dentro de `Clinical response` aparecen BP, SpO₂ y también los objetivos solicitados que no cambiaron: `CRT 8 s → 8 s` y `Extremities mottled/cold → mottled/cold`;
- `New diagnostic information` muestra el lactato nuevo de `6.7 mmol/L`;
- Management reasoning muestra por separado `Expected effect: improved blood pressure, capillary refill, and lactate` y `Preservation goal: preserve oxygenation`;
- Reflect & Compare explica que las mejoras esperadas no se demostraron y, en una oración separada, que la oxigenación también empeoró a pesar del objetivo de preservarla;
- las tres tarjetas esperadas de Reflect & Compare corresponden a las Decisiones 2, 9 y 11.

## Prueba longitudinal preservada de v0.7.13

Después de completar la trayectoria:

- en la Decisión 4 debe aparecer `Mental status alert → sedated after intubation`;
- en la Decisión 5 debe aparecer `Mental status sedated → sedated`, sin repetir `after intubation`;
- la HR debe evolucionar gradualmente y terminar aproximadamente en `128/min`, no permanecer fija en 124/min;
- abre `Patient Data → Treatments` y confirma:
  - `Norepinephrine: 0.3 mcg/kg/min — started 00:25 · last adjusted 01:35`;
  - `Dobutamine: 2.5 mcg/kg/min — started 01:35`;
  - `Invasive ventilation: VC/AC · FiO₂ 60% · PEEP 10 cm H2O — started 00:30 · last adjusted 01:35`.

## Temporalidad diagnóstica preservada de v0.7.12

Después de completar las once entradas, abre `Patient Data → Diagnostics`.

Esperado:

- `POCUS · 01:32` identifica el estudio más reciente;
- `Lactate · 01:45` identifica el resultado repetido más reciente;
- `ABG · 01:13` conserva la hora de la gasometría;
- los tiempos permiten distinguir resultados históricos de los ajustes actuales de PEEP y vasopresores.

### Control del último PEEP explícito

Con ventilación invasiva activa, también puedes probar:

```text
The prior POCUS was obtained while the patient was on PEEP 14 cm H2O. My working model is that high intrathoracic pressure may be worsening forward flow despite acceptable oxygenation. My priority is to reduce the pressure burden while preserving gas exchange. Reduce PEEP to 10 cm H2O. I expect improved perfusion without clinically important loss of oxygenation. Reassess perfusion and oxygenation in 5 minutes.
```

El simulador debe aplicar `PEEP 10 cm H₂O`, no reutilizar el 14 mencionado retrospectivamente.

## Control opcional de POCUS sin presión positiva

Reinicia PS002 y solicita POCUS antes de iniciar NIV o intubación:

```text
Obtain a POCUS and reassess in 5 minutes.
```

En respiración espontánea, el informe puede conservar la descripción de variación respiratoria de la VCI. La advertencia específica de presión positiva solo debe aparecer cuando NIV o ventilación invasiva estén activas.

## Cerrar el Caso 2 y probar Decision Review

1. Después de la Entrada 11, pulsa `Complete Encounter & Begin Review`.
2. Confirma que desaparece el formulario de nuevas órdenes y que aparece el Management Trace congelado.
3. Confirma que Decision Review selecciona las Decisiones 2, 9 y 11.
4. Verifica que los botones `Download PDF`, `Download Markdown` y `Download JSON` ya estén visibles en la parte superior; en este momento permiten descargar un borrador.
5. Confirma que el indicador inicia en `0/24 fields autosaved`, `0/3 decisions`, `0/3 comparisons` y `0/6 plan fields`.
6. Solo la Decisión 2 debe estar expandida. Las Decisiones 9 y 11 deben aparecer como tarjetas cerradas bajo `Other review points`.
7. Completa los cuatro campos de la Decisión 2 con los textos siguientes y pulsa `Next decision`. No debe existir un botón manual de guardado.
8. Confirma que el progreso y el estado de la tarjeta cambian al salir de la decisión: esto verifica el autosave.
9. Repite el proceso para la Decisión 9 y luego la Decisión 11. También puedes usar `Review this decision` para saltar directamente a una tarjeta cerrada.
10. Antes de completar las doce respuestas, `Expert Comparison`, `Adaptation Plan` y `Final Summary` deben permanecer bloqueados.
11. Un PDF, Markdown o JSON descargado en este momento no debe contener el texto del modelo experto.

### Decision 2

**How has your working model changed?**

```text
The blood-pressure response to fluid did not resolve shock: tachycardia, prolonged capillary refill, elevated lactate, and severe hypoxemia persisted. I would retain mixed distributive/low-flow shock with respiratory failure rather than conclude that shock had resolved.
```

**What finding or threshold should influence your next priority?**

```text
Persistent CRT 4 seconds and lactate 4.7 mmol/L despite BP improvement, especially with worsening work of breathing, should prevent further reassurance from pressure alone.
```

**What alternative action would you take?**

```text
Escalate oxygen support while explicitly limiting further fluid, prepare vasopressor support, and reassess pressure and peripheral perfusion early.
```

**What response would you expect, and what would you reassess?**

```text
I would expect improved oxygenation without worsening pressure or CRT and would reassess BP, CRT, extremities, mental status, SpO2, and work of breathing within 5–10 minutes.
```

### Decision 9

**How has your working model changed?**

```text
The minimal pressure response with worsening CRT, cold extremities, and lactate supports pressure–flow dissociation; simply increasing vasoconstriction may not restore tissue perfusion.
```

**What finding or threshold should influence your next priority?**

```text
Failure of CRT or lactate to improve after a MAP-directed norepinephrine titration should trigger reassessment of forward flow and intrathoracic-pressure burden.
```

**What alternative action would you take?**

```text
Repeat POCUS, reassess LV/RV function and congestion, and consider reducing excessive PEEP or adding inotropic support based on the phenotype.
```

**What response would you expect, and what would you reassess?**

```text
I would expect a phenotype-directed change to improve CRT, extremity temperature, and lactate while preserving oxygenation; reassess in 5–10 minutes.
```

### Decision 11

**How has your working model changed?**

```text
Persistent poor perfusion despite improved pressure and preserved/hyperdynamic LV appearance suggests that macro-hemodynamic pressure and tissue flow remain dissociated.
```

**What finding or threshold should influence your next priority?**

```text
No improvement in CRT or lactate after the combined PEEP, norepinephrine, and dobutamine change should trigger another immediate reassessment instead of automatic dose escalation.
```

**What alternative action would you take?**

```text
Recheck the hemodynamic phenotype, verify the treatment response and measurement trend, and revise support one variable at a time with a predefined stop threshold.
```

**What response would you expect, and what would you reassess?**

```text
I would expect improving peripheral perfusion and lactate without loss of pressure or oxygenation and would reassess BP, CRT, extremities, SpO2, and lactate within 5–10 minutes.
```

## Expert Comparison

Después de completar los cuatro campos de las Decisiones 2, 9 y 11:

1. Pulsa `Lock Decision Review & Reveal Expert Comparison`.
2. Confirma que la aplicación abre `2 · Expert Comparison`.
3. Regresa momentáneamente a `1 · Decision Review`: los doce campos deben estar visibles, pero bloqueados para edición.
4. Confirma que cada comparación identifica el contenido como `faculty-validation draft`, `not an answer key` y `non-scoring`.
5. Revisa que cada modelo muestre por separado: framing, management priority, key cues, one defensible action, trade-off y reassessment targets.
6. Completa los dos campos de comparación de cada decisión con los textos siguientes.

### Comparison · Decision 2

**Where did your reasoning align with this model?**

```text
I recognized that the modest pressure response did not resolve shock and that respiratory escalation required close reassessment of both oxygenation and perfusion.
```

**What will you change or preserve next time?**

```text
Before escalating positive-pressure support, I will explicitly anticipate its effect on venous return, ensure vasopressor support is prepared when indicated, and reassess perfusion within about 5 minutes.
```

### Comparison · Decision 9

**Where did your reasoning align with this model?**

```text
I recognized pressure–flow dissociation and the need to repeat focused POCUS before continuing automatic vasopressor escalation.
```

**What will you change or preserve next time?**

```text
I will not interpret an acceptable SpO2 on high FiO2 as normal gas exchange, and I will integrate the P/F ratio, tissue-perfusion markers, and ventilator burden before selecting the next intervention.
```

### Comparison · Decision 11

**Where did your reasoning align with this model?**

```text
I targeted forward flow and intrathoracic-pressure burden while trying to preserve both arterial pressure and oxygenation.
```

**What will you change or preserve next time?**

```text
When clinically feasible, I will change one support variable at a time with predefined response and stopping thresholds so that I can identify benefit, harm, and the intervention responsible.
```

Después de completar la Decisión 11, el progreso debe mostrar `3/3 comparisons`. Pulsa `Continue to Adaptation Plan`.

## Adaptation Plan

El Adaptation Plan aparece solamente después de revelar la comparación. Los cinco borradores siguen proviniendo de la reflexión original bloqueada, no del texto experto.

Antes de editar, verifica que:

- cinco campos contienen borradores construidos exclusivamente a partir de tus reflexiones;
- `Clinical cue to watch` termina después del hallazgo observado y no contiene la acción alternativa;
- `Threshold for changing course` comienza con el umbral completo y no a mitad de una frase;
- `Clinical cue to watch` y `Threshold for changing course` no son copias idénticas;
- `Next management priority` permanece vacío porque no debe inventarse una prioridad que el usuario no escribió;
- todos los campos siguen siendo editables;
- si modificas un borrador y navegas a otra etapa, tu texto no es sobrescrito al regresar.

Completa o reemplaza los seis campos así:

- **Clinical cue to watch:** `A mismatch between acceptable MAP and worsening CRT, extremity temperature, or lactate.`
- **Threshold for changing course:** `No peripheral-perfusion improvement within 5–10 minutes, or any worsening after an intervention.`
- **Next management priority:** `Reassess pressure, forward flow, and respiratory-support burden before further escalation.`
- **Alternative action:** `Repeat focused POCUS and adjust one support variable at a time according to the observed phenotype.`
- **Expected effect:** `Improved tissue-perfusion markers while preserving adequate pressure and oxygenation.`
- **Reassessment target and timing:** `BP/MAP, CRT, extremities, SpO2, and lactate; bedside reassessment in 5–10 minutes and repeat lactate at the planned interval.`

Pulsa `Continue to Final Summary`. Debe aparecer un resumen compacto y el indicador debe mostrar `24/24 fields autosaved`, `3/3 decisions`, `3/3 comparisons`, `6/6 plan fields` y `Complete`.

Verifica que el resumen muestre Decision synthesis, Comparison synthesis y un Adaptation Plan compacto. `View Locked Review` debe permitir consultar, pero no modificar, la reflexión original; `Edit Comparison` y `Edit Adaptation Plan` deben conservar los cambios mediante autosave.

## Adapt & Repeat

1. Descarga primero el reporte completo del intento 1.
2. Confirma que aparece el botón `Repeat Encounter with This Adaptation Plan`; solo debe estar habilitado cuando el resumen indique `Complete`.
3. Púlsalo y comprueba que:

   - el encabezado muestra `Attempt 2 · Carry-Forward Learning Goal`;
   - aparecen los seis campos del Adaptation Plan anterior;
   - `Clinical Encounter` contiene solamente la presentación inicial nueva;
   - Patient Data vuelve al estado inicial de PS002;
   - Management Trace, Decision Review y Expert Comparison comienzan vacíos;
   - aparecen `Previous PDF`, `Previous Markdown` y `Previous JSON` para recuperar el reporte completo del intento 1.

4. Descarga `Previous PDF` y confirma que conserva la trayectoria, reflexión, comparación y Adaptation Plan del intento 1 en páginas imprimibles.
5. Ejecuta al menos una orden nueva en el intento 2 y confirma que su Management Trace registra únicamente esa nueva decisión.
6. Si cierras y exportas el intento 2, el JSON debe incluir:

```text
schema: management_reasoning_decision_review_v3
learning_cycle.attempt_number: 2
learning_cycle.carry_forward_plan
learning_cycle.prior_attempt_summary
```

El plan visible funciona como intención prospectiva: no debe aparecer automáticamente como una acción realizada en el nuevo Management Trace.

### Exportación

1. Confirma que `Download PDF`, `Download Markdown` y `Download JSON` permanecen visibles tanto en la parte superior como al final del resumen.
2. Pulsa `Download PDF` y abre `ps002_decision_review_v0819.pdf`.
3. Confirma que el PDF tenga páginas legibles, encabezado y numeración repetidos, estado `Complete`, y las secciones `Management Trace`, `Decision Review`, `Expert Comparison` y `Prospective Adaptation Plan`.
4. Pulsa `Download Markdown` y abre `ps002_decision_review_v0819.md`; verifica las mismas cuatro capas educativas.
5. Pulsa `Download JSON`, abre `ps002_decision_review_v0819.json` y verifica que tenga `schema: management_reasoning_decision_review_v3`.
6. Busca `physiology`, `hidden` y `forward_flow_state`: no deben aparecer en ninguno de los tres archivos.
7. Confirma que el Management Trace conserva las órdenes originales, las respuestas retrospectivas aparecen solo bajo Decision Review y los modelos/insights aparecen únicamente bajo Expert Comparison.

## Prueba automatizada

```bash
cd ~/Downloads/management_reasoning_simulator_v0.8.21
python3 -m py_compile app.py
python3 run_regressions.py
```

Resultado esperado:

```text
PASS: 53 active regression scripts
```
