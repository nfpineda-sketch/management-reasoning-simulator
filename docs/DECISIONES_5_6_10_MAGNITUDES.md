# Bloqueo AV, inótropo y morfina — magnitudes implementadas

> **Estado: IMPLEMENTADO** el 2026-09-21 en `bradycardia_support.py`, `inotrope_support.py` y
> `analgesia.py`, con las decisiones docentes 5, 6 y 10 de la revisión del banco. Son
> parámetros docentes, no un modelo farmacológico. Las trayectorias de abajo salen del motor
> ya implementado. Las familias que no tocan estos fármacos dan exactamente lo mismo que antes.

## Decisión 5 · El bloqueo AV completo tiene tratamiento

Antes: el bloqueo aparecía solo a los 45 minutos del infarto inferior, la frecuencia caía a 42
y el residente no tenía nada que ofrecer. Ahora el bloqueo **cuesta presión** y esa presión se
recupera cuando se recupera la frecuencia.

### Dónde está el bloqueo

| Caso | Localización | Respuesta a atropina |
|---|---|---|
| Territorio **inferior** (o el caso lo declara `nodal`) | **nodal** | sí, parcial y transitoria |
| Cualquier otro territorio, o `av_block_location: infranodal` | **infranodal** | no: sube la aurícula, el ventrículo no sigue |

### Atropina

| Mecanismo | Magnitud |
|---|---|
| Dosis | **1 mg IV**, repetible; máximo acumulado **3 mg** |
| Sobre el máximo | No se administra, y el registro dice que este bloqueo necesita marcapasos |
| Primera dosis, bloqueo nodal | **+18 latidos** |
| Cada dosis siguiente | **×0.55** de la anterior (18 → 9.9 → 5.4) |
| Desvanecimiento | Constante de **12 minutos**: a los 12 min queda la mitad |
| Bloqueo infranodal | **0 latidos**, y el registro lo dice |

### Marcapasos transcutáneo

| Mecanismo | Magnitud |
|---|---|
| Orden | Exige **frecuencia** (30–100/min) **y corriente** (1–200 mA): elegir una frecuencia no es marcapasear |
| Umbral de captura | **70 mA** en este paciente |
| Sin captura | Espigas sin complejo, sin efecto hemodinámico, y el ritmo del monitor lo dice |
| Con captura | La frecuencia ventricular es la programada, con pulso palpable |
| Eficiencia del latido estimulado | **0.85**: un latido estimulado no es el latido propio |
| Presión que devuelve | **34 mmHg** por la fracción de frecuencia perdida, proporcional |

### Trayectoria del motor (54m, infarto inferior con compromiso de VD)

| Momento | PA | FC | Ritmo |
|---|---|---|---|
| 50 min (bloqueo instalado) | 84/55 | 42 | Bloqueo AV completo |
| +atropina 1 mg | 91/59 | 55 | Bloqueo AV completo |
| +10 min (se desvanece) | 90/59 | 55 → 53 | Bloqueo AV completo |
| Marcapasos 70/min a **50 mA** | 88/57 | 53 | **Espigas sin captura** |
| Marcapasos 70/min a **90 mA** | 91/59 | **70** | **Captura confirmada** |
| Atropina por sobre 3 mg | sin cambios | | la orden se retiene y se explica |

**Lo que no hace**: el marcapasos no resuelve el shock. La presión que devuelve es la que la
bradicardia estaba costando, y nada más: el ventrículo infartado, el VD y la reperfusión
pendiente siguen ahí.

## Decisión 6 · Dobutamina en cualquier familia

Antes respondía *"This intervention requires a generated encounter with an explicit response
rule"* en un shock cardiogénico por tronco. Ahora existe en todas las familias, con el mismo
motor, y **nunca es una mejoría automática**.

| Mecanismo | Magnitud |
|---|---|
| Alivio máximo de la carga de bajo gasto | **0.35** unidades de circulación |
| Dosis de medio efecto | **5 mcg/kg/min** (satura: 5 → 0.175, 10 → 0.23, 20 → 0.28) |
| Instalación del efecto | Constante de **3 minutos** |
| Cronotropismo | **+2.2 latidos por mcg/kg/min**, sin techo propio |
| Vasodilatación | **−0.9 mmHg de PAS por mcg/kg/min**, que pelea contra la ganancia |
| Arritmia | Sobre **10 mcg/kg/min**: evento en el registro y **+14 latidos** adicionales |

### Cuánto de la carga puede levantar un inótropo puro, por familia

| Familia | Fracción contráctil |
|---|---|
| SCA | **1.00** |
| Edema pulmonar | 0.60 |
| Neumonía | 0.20 |
| TEP | **0.15** — un ventrículo derecho obstruido no es una falla contráctil |
| Hemorragia digestiva | 0.10 |
| Asma, hipoglicemia, opioides | 0.10 |

### Trayectoria del motor (70f, tronco coronario izquierdo)

| Orden | PA | FC | Llene |
|---|---|---|---|
| Reperfusión activada | 102/65 | 113 | 3.2 |
| **Dobutamina 5 mcg/kg/min** | 100/63 | **123** | **3.0** |
| **Dobutamina 12 mcg/kg/min** | **93/60** | **152** | 3.0 · *ectopia ventricular en el registro* |
| De vuelta a 5 | 99/63 | 123 | 3.0 |
| + noradrenalina 0.1 | **110/70** | 123 | 3.0 |

La lectura docente está en la tercera fila: **subir el inótropo bajó la presión y subió la
frecuencia**. La presión la recupera el vasopresor, no más inótropo.

## Decisión 10 · Morfina

Existe en todas las familias. Reconocer la orden no es aprobarla.

| Mecanismo | Magnitud |
|---|---|
| Dolor de llegada | SCA **7/10**, TEP 4, hemorragia digestiva 2, neumonía 2, edema 2, asma 1, hipoglicemia y opioides 0 |
| Analgesia máxima | **7 puntos**, con dosis de medio efecto de **4 mg** |
| Instalación / eliminación | Constantes de **4 min** y **150 min** |
| Venodilatación | **1.1 mmHg de PAS por mg**, con constante de **6 minutos** |
| Vulnerabilidad · **VD precargo-dependiente** | **×2.2** |
| Vulnerabilidad · circulación sangrante | ×2.0 |
| Vulnerabilidad · paciente con PAS ≥ 130 | **×0.35** |
| Sedación | Sobre **11 mg** acumulados, un escalón; sobre 20 mg, dos |
| Frecuencia respiratoria | **−0.8/min por mg** por sobre los 11 mg |
| Náuseas y vómitos | Sobre **6 mg** en los pacientes susceptibles, que son **dos de cada tres** (por semilla del caso, no por minuto) |
| Naloxona | Revierte el efecto, no el fármaco: **vuelve el dolor** junto con la ventilación |
| Arteria abierta | El dolor basal baja a **2/10**: la reperfusión es la analgesia |

### El mismo fármaco en dos pacientes

| Paciente | Dosis | PA antes → después | Dolor | Conciencia |
|---|---|---|---|---|
| **54m inferior con VD** (PAS 98) | 4 mg | **98 → 88** | severo → moderado | alerta |
| mismo paciente, acumulado 10 mg | +6 mg | **88 → 64** | moderado → leve | **obnubilado** · vómitos |
| tras naloxona 0.4 mg | — | 64 → **80** | **vuelve a severo** | **alerta** |
| **66f NSTEMI** (PAS 146) | 4 mg | **146 → 144** | severo → moderado | alerta |

## Qué se agregó al registro

- **El dolor es visible**: la tarjeta de respuesta termina con *"The patient reports severe /
  moderate / mild / no pain"*, y `pain_score` (0–10) está en el observable.
- El ritmo del monitor dice **"Pacing spikes without capture"** o **"Paced rhythm, capture
  confirmed"**, no solo la frecuencia.

## Fuera de este cambio

- **Vía aérea y drogas de intubación** (decisión 11): rocuronio y las infusiones de sedación
  siguen sin existir.
- **Absorción de los antiagregantes orales** tras el vómito: el evento avisa que lo dado por
  boca queda de absorción incierta, pero no se modela la demora del P2Y12.
- **Aspiración** con compromiso de conciencia: no se modela.
- **Adrenalina o dopamina como puente** en el bloqueo: no se agregaron; la adrenalina ya existe
  en el motor pero no está conectada a esta decisión.
- **Marcapasos transvenoso**: no existe; la solicitud queda como interconsulta.
- **Los casos generados por IA** no usan estas ramas: tienen sus propios mecanismos declarados.
