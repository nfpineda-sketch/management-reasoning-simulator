# Techo de recuperación, opioide corto, volumen y vía perdida — magnitudes implementadas

> **Estado: IMPLEMENTADO** el 2026-09-22 en `acs_reperfusion.py`, `opioid_reversal.py`,
> `preload_response.py` y `glucose_rescue.py`, con las decisiones docentes 3, 3b, 4 y 8.

## Decisión 3 · El paciente tratado a tiempo queda mejor que como llegó

Tu respuesta: *"paciente que llega con patologías agudas tiempo dependientes, es esperable que
si se hacen las cosas bien, finalmente esté en mejores condiciones clínicas que las en que
llegó… incluso estos pacientes en el t0, cuando tienen un evento agudo, su basal empeora y
llegan peor al servicio de urgencia."*

| Antes | Ahora |
|---|---|
| La recuperación del SCA se detenía **exactamente en el estado de llegada** | Se detiene en la **circulación previa al evento**: `CIRCULATION_ARRIVAL = 0.85` |

La llegada es la basal del paciente **más** el evento agudo. Reperfundir devuelve lo que la
oclusión quitó, y eso deja al paciente por sobre la llegada: en el inferior reperfundido el
llene capilar cierra en 2.7 s contra los 3.0 s con que entró.

**El dolor sigue la misma regla**: con la arteria abierta el dolor basal baja a **cero**, no a
un piso residual. Era la pregunta que te dejé abierta; la resolví en esa dirección porque es la
misma decisión, y el evento de reperfusión ya dice *"the discomfort settles"*.

## Decisión 3b · Concentración y efecto no son lo mismo

Tu instrucción fue corregir el modelo de efecto **antes** de volver a tocar la vida media.

| Mecanismo | Magnitud |
|---|---|
| Umbral de **efecto ventilatorio** | **0.50** de agonista libre |
| Umbral de **efecto sobre la conciencia** | **0.32** |
| Absorción oral | **3.5%/min** del depósito (semivida de absorción ~20 min) |
| Depósito del 35m al llegar | **0.33**: un tercio del comprimido todavía sin absorber |
| Vida media de eliminación | **sin cambios**: 4 h el corto, y el largo sigue siendo largo |

Las dos consecuencias que pediste:

- **La ventilación se recupera antes que la conciencia.** Es la misma enseñanza del antídoto:
  se titula a la ventilación, y el paciente puede respirar bien y seguir demasiado somnoliento
  para irse a la casa.
- **La recuperación no espera a que la concentración llegue a cero.** El 35m queda **alerta con
  esfuerzo normal a los 380 minutos con el opioide todavía en 0.45**, y el alta se sostiene sin
  que vuelva.

La curva ahora **sube antes de bajar**: a los 80 minutos la concentración está en 1.06, por
encima de la de llegada, porque el comprimido se sigue absorbiendo mientras el residente decide.

## Decisión 4 · El volumen responde a la hemodinamia, no al antecedente de nitratos

| Mecanismo | Magnitud |
|---|---|
| Ganancia | **0.00040 de carga circulatoria por mL**, a respuesta plena |
| Tolerancia | **1600 mL** con compromiso del VD · **700 mL** si el problema es el VI · 1000 mL en el resto |
| Respuesta restante | `1 − acumulado / tolerancia`: cada bolo rinde menos que el anterior |
| Parte precargo-dependiente | **1.0** en el VD · **0.25** en el VI · 0.6 en el resto |
| Pasada la tolerancia | **0.00035 de carga pulmonar por mL** y la presión deja de responder |

### Los dos ventrículos, con el mismo bolo

| | Infarto inferior con VD | Tronco coronario izquierdo |
|---|---|---|
| Llegada | 100/64 · llene 3.0 | 104/66 · llene 3.0 |
| +500 mL | **105/67 · llene 2.6** | 103/66 · llene 3.1 |
| +1000 mL | **107/68 · llene 2.4** | 102/65 · llene 3.2 · **advertencia de sobrecarga** |
| +1500 y más | la presión deja de responder | sigue cayendo |

La advertencia dice: *"1633 mL of crystalloid is past what this ventricle is carrying: the
pressure has stopped answering and the lungs are starting to. Reassess tolerance before the
next bolus."* La conducta que queda enseñada es **bolo prudente → reevaluar → adaptar**, nunca
"infarto de VD, entonces volumen ilimitado". La reperfusión sigue debiéndose igual.

## Decisión 8 · Una dosis indicada no es una dosis recibida

Retiraste la encefalopatía de Wernicke establecida. El caso del 54m ahora enseña otra cosa.

| Antes | Ahora |
|---|---|
| Glucosa sin tiamina dejaba al paciente **confuso** | **Se eliminó**. La glucosa que llega corrige la glicemia y la conciencia con ella |
| La tiamina despertaba al paciente | La tiamina **no cambia la conciencia**, y su omisión no deteriora |
| Nada fallaba en la administración | **La vía con que llega no está en la vena** |

| Mecanismo | Magnitud |
|---|---|
| Fracción que llega por una vía perdida | **15%** |
| Cómo se detecta | Visible al lado de la cama: *"the forearm swells around the cannula and the infusion slows to a stop"* |
| Cómo se corrige | `Instala una vía venosa periférica` → *"The new line runs freely"* |
| Glucagón con hígado depletado | **30%** de la respuesta normal: no ha comido en días |

### La trayectoria

| Turno | Glicemia | Estado |
|---|---|---|
| 25 g IV por la vía que trae | 32 → **45** | somnoliento, y el antebrazo hinchado en el registro |
| control a los 20 min | 45 → 44 | **obnubilado**: no basta con haber indicado |
| vía nueva | — | *"La vía nueva pasa sin resistencia"* |
| 25 g IV de verdad | 43 → **142** | **alerta** |
| tiamina 500 mg IV | sin cambio neurológico | objetivo secundario, cumplido |

**El residente resuelve la emergencia completa sin indicar tiamina jamás**, que era tu criterio
de aceptación.

## Fuera de este cambio

- **La vía perdida solo afecta a la glucosa endovenosa** de este caso. Extenderla a todo fármaco
  IV es posible, pero cambiaría todas las familias y no es lo que la decisión pedía.
- **El octreotide, el carbohidrato oral y la infusión al 10%** siguen como estaban.
- **No se tocó ninguna vida media**, como pediste.
- **Los casos generados por IA** no tienen la vía perdida ni el depósito de absorción; la
  instrucción del generador ya no menciona la encefalopatía retirada.
