# Vía aérea, soporte, diuresis y confort — magnitudes implementadas

> **Estado: IMPLEMENTADO** el 2026-09-21 en `airway_pharmacology.py`, `urine_output.py`,
> `antipyretics.py` y las ramas de soporte de `family_engine.py`, con las decisiones docentes
> 11, 12, 13 y 14 de la revisión del banco.

## Decisión 11 · Inducción, parálisis y mantención

Tres cosas que antes eran una sola. **El bloqueo saca movimiento y no saca nada más**: no seda,
no analgesia, y un paciente que no se mueve no es un paciente sedado.

### Reconocimiento de órdenes

| Se escribe | Se entiende |
|---|---|
| `ketamina 2 mg/kg`, `rocuronio 1.2 mg/kg` | dosis por peso, con el peso del caso |
| `propofol a 2 mg/kg/h`, `fentanilo a 1 mcg/kg/h` | **infusión**, que persiste, se titula y se suspende |
| `Intuba en secuencia rápida con ketamina 2 mg/kg y rocuronio 1.2 mg/kg, en VC/AC con FiO2 100%, PEEP 5, volumen corriente 6 mL/kg y frecuencia 10` | **una** orden con tres componentes confirmados, y los parámetros quedan en el tubo |

La vía del relajante no se pregunta: no tiene otra.

### Bloqueadores

| Fármaco | Dosis de referencia | Inicio | Duración |
|---|---|---|---|
| Rocuronio | 1.0 mg/kg | 1 min | 45 min |
| Succinilcolina | 1.5 mg/kg | 1 min | 8 min |
| Vecuronio | 0.1 mg/kg | 2 min | 40 min |
| Cisatracurio | 0.15 mg/kg | 3 min | 50 min |

La duración escala con la dosis, con tope de **×2**: una dosis doble no dura cuatro veces más.

### Lo que el motor informa

| Situación | Estado mental | Trabajo respiratorio |
|---|---|---|
| Sedado (inducción vigente o infusión corriendo) | Sedated | Ventilator-supported |
| **Bloqueado sin sedación** | **Paralysed, sedation not maintained** | Ventilator-supported, no spontaneous effort |
| Ni una cosa ni la otra | Awake and fighting the ventilator | Ventilator dyssynchrony |

Y dos eventos de seguridad:

- **"The blocker is still working and the hypnotic is not"** cuando el bloqueo sobrevive al
  hipnótico. En el asma 49m intubado con ketamina y rocuronio y sin mantención, aparece al
  minuto 46.
- **Paro cardíaco a los 8 minutos** de parálisis sin ventilación: *"The blocker removed every
  breath the patient had; the ventilation that replaces them was never established."*

### Infusión de mantención

| Fármaco | Costo de presión a dosis de referencia | Dosis de referencia |
|---|---|---|
| Propofol | **12 mmHg** | 3 mg/kg/h |
| Dexmedetomidina | 8 mmHg | 0.001 mg/kg/h |
| Midazolam | 6 mmHg | 0.1 mg/kg/h |
| Fentanilo | 3 mmHg | 0.002 mg/kg/h · **es analgesia, no sedación** |
| Ketamina | 0 | 1 mg/kg/h |

En el asma intubado: propofol 3 mg/kg/h baja la presión de 141 a 129 y **sostiene la sedación**;
al suspenderlo el paciente vuelve a *Awake and fighting the ventilator* con disincronía.

**Lo que el bloqueo no hace**: no toca la resistencia bronquial. Quita las respiraciones propias,
y el atrapamiento cambia a través de la mecánica, no porque se haya dado el fármaco.

## Decisión 12 · La diuresis se produce, y alguien la mide

Tres cosas separadas: **administración**, **producción** y **medición**.

| Mecanismo | Magnitud |
|---|---|
| Producción basal | **1.0 mL/kg/h** con perfusión normal |
| Perfusión | Se pierde **1.6 × la carga de circulación**: oliguria mucho antes que anuria, anuria sobre 1.625 |
| Furosemida, inicio | **20 min** IV, **45 min** oral |
| Furosemida, magnitud | **6 mL por mg** a respuesta plena, decayendo con τ de **90 min** |
| Creatinina | Media respuesta con creatinina 3.2 mg/dL (τ 2.2 sobre la basal) |
| Dosis sucesivas | **×0.7** cada una respecto de la anterior |
| Lectura con sonda | Cada **30 minutos**, con volumen, intervalo y mL/h |
| Sin sonda | El paciente **orina** al acumular 250 mL, y el registro dice que **no está cuantificada** |

Ejemplo real del motor (edema pulmonar 75f, sonda instalada, furosemida 40 mg IV):

| Intervalo | Volumen | Tasa |
|---|---|---|
| 0–30 min | 37 mL | 74 mL/h |
| 30–60 min | **85 mL** | **169 mL/h** |
| 60–90 min | 71 mL | 141 mL/h |
| 90–120 min | 60 mL | 121 mL/h |
| 120–150 min | 53 mL | 107 mL/h |

**La respuesta no está condicionada a que el edema ceda primero**, y la sonda mide: no produce.

## Decisión 13 · Las órdenes de enfermería son órdenes

| Orden | Estado y efecto |
|---|---|
| Vía venosa periférica | Registrada. Los casos del banco **ya tienen** acceso: la orden lo confirma y el registro lo dice |
| Monitor y oximetría | Registrado: *"the monitor is on; it watches the patient and treats nothing"* |
| Régimen cero | Registrado |
| Sonda Foley | **Habilita la medición** de diuresis |
| Sonda nasogástrica | Registrada; para qué es, depende de la indicación |

- Ninguna cambia la fisiología.
- Duran entre 1 y 4 minutos; **no cuestan el turno completo**, y varias caben en una sola orden.
- Repetir una que ya está puesta responde **"already in place; not repeated"** y cuesta 0 minutos.
- `Monitoriza presión arterial y saturación` sigue siendo una **reevaluación**, no un monitor.

## Decisión 14 · Analgésicos y antipiréticos

| Fármaco | Caída máxima | Analgesia máxima | Inicio IV | Dosis de referencia |
|---|---|---|---|---|
| Paracetamol | 1.1 °C | 2.0 puntos | 20 min | 1000 mg |
| Ibuprofeno | 1.2 °C | 2.5 | 25 min | 600 mg |
| Metamizol | 1.2 °C | 2.5 | 20 min | 1000 mg |
| **Ketorolaco** | **0.6 °C** | **3.0** | 20 min | 30 mg |

- La **vía oral suma 20 minutos** de inicio, y se **retiene** si el paciente no está alerta:
  *"withheld by mouth: the patient is drowsy and swallowing is not safe"*.
- El efecto se agota en **4 horas** y la fiebre vuelve mientras la infección siga.
- **Nunca baja de 37.5 °C**: un antipirético no enfría a nadie.
- **Ketorolaco no es la opción antipirética de referencia**: su caída es la mitad.

### Precauciones que sí se revisan

- **Dos AINE son una clase**: *"ketorolac on top of ibuprofen: two NSAIDs are one class. The
  second adds the risks and very little of the effect."*
- AINE con **creatinina ≥ 1.5**, con **mala perfusión** (carga ≥ 0.15) o en la **hemorragia
  digestiva**: el registro nombra la razón y devuelve la decisión al residente.

Trayectoria real (neumonía 46f, fiebre 39.1): paracetamol 1 g IV → **38.0 a los 30 min**, 38.3
a los 90 cuando se agota, ibuprofeno 600 mg IV → **37.6**, y el piso de 37.5 se sostiene.

## Fuera de este cambio

- **La absorción de los antiagregantes orales** tras el vómito sigue sin modelarse.
- **Aspiración** con compromiso de conciencia: no se modela.
- **El acceso venoso no condiciona** la administración IV en los casos del banco: todos llegan
  con vía. Un caso que quiera enseñar la vía perdida tendría que declararlo.
- **La sonda nasogástrica no drena nada** todavía; queda registrada.
- **El traslado a pabellón** sigue pidiendo destino como cualquier traslado.
- **Los casos generados por IA** no ejecutan ninguno de estos fármacos ni órdenes: el catálogo
  que se le ofrece al autor no los incluye.
