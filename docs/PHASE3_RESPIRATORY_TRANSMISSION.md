# Fase 3 · La transmisión hipoventilación → oxigenación (P3-117 a P3-126)

Rama `phase-3-runtime-integration`. Base `0aee3b3`. El motor de familias heredado sigue siendo la única
autoridad en tiempo de ejecución (`COMMON_CORE_RUNTIME_AUTHORITY = False`), nada de esto llega al residente
y nada entra en la puntuación. El enlace común de P2T-5 sigue **UNSET** en todos los perfiles comprometidos:
este ciclo lo **midió**, no lo encendió.

Fuente de los números: `respiratory_transmission_record.py`, verificado por `test_respiratory_transmission.py`
(27 pruebas). Las decisiones correspondientes son FD-P3-104 a FD-P3-115.

## 1 · La ecuación, entera (P3-117-1)

| # | Eslabón | De dónde sale | Estado |
|---|---|---|---|
| 1 | FR expresada | la composición común del impulso respiratorio (P2P-2) | ADOPTED |
| 2 | `W = eficiencia · FR / FR_intrínseca / razón_de_demanda` | `derived.alveolar_ventilation` | ADOPTED |
| 3 | `PaCO2 = paco2_reference_mmhg / W` | candidato de mecánica común (P2S-2) | PROVISIONAL |
| 4 | `PaCO2_llegada = paco2_reference_mmhg / W_llegada` | `derived.arrival_paco2_reference` | PROVISIONAL |
| 5 | `delta = PaCO2 − PaCO2_llegada` | la forma relativa; Patm, PH2O y el gas alveolar absoluto se cancelan | PROVISIONAL |
| 6 | `PaO2_latente = ODC⁻¹(SpO2_base)` | `derived.pao2_from_oxygen_saturation` (Severinghaus 1979, sin parámetro ajustado) | ADOPTED |
| 7 | `dPaO2 = −delta / R` | `derived.ventilated_oxygenation` (P2T-5) | **UNSET** |
| 8 | `SpO2 = ODC(PaO2_latente + dPaO2)` | `derived.oxygen_saturation_from_pao2` | ADOPTED |

`SpO2_base` es la vía ya certificada `G / L → G / FiO2` (P2O-3): el enlace la mueve, no la reemplaza. PaO2 es
latente y nunca es estado. **Uno solo** de los ocho eslabones está UNSET.

Dos cosas que no se esperaban y hay que decir: el candidato de mecánica común **ya está encendido** en los
perfiles de opioide y de asma (`respiratory_mechanics = True`, `acid_to_drive_gain = 2.0`), y el validador
**rechaza** `ventilation_efficiency != 1.0` cuando lo está, así que ese mando está cerrado por construcción.

## 2 · Los tres mandos candidatos: ninguno es un coeficiente de transmisión

| Mando | Cómo entra | La región exigiría | Veredicto |
|---|---|---|---|
| `respiratory_quotient` | divide el delta; `f = 1/R` | **R ≥ 13,1968** | escala la transmisión, **pero no es un coeficiente de transmisión**: es un cociente respiratorio, ~0,7–1,0 |
| `paco2_reference_mmhg` | escala el delta linealmente | **≈3,03 mmHg** | falsifica su cantidad declarada: el PaCO2(60) del caso pasa a **7,061 mmHg**, imposible, y el campo es común a todas las familias |
| `rr_ventilatory_floor` | hipótesis: fija la FR intrínseca | — | **hipótesis falsificada por medición**: el delta(60) vale 24,2104 con el piso en 0,0, 3,0, 6,0, 12,0 y 18,0 |

El álgebra de la tercera hipótesis era correcta —el delta es lineal en la FR intrínseca— y la medición la
descartó igual: el piso no alcanza a la FR intrínseca de este caso. Se deja escrita porque una hipótesis
falsificada por datos vale más que una no formulada.

## 3 · La región admisible (P3-117-3)

Invirtiendo la decisión docente SpO2(60) ∈ [78, 88] %. El techo de 88 % **no ata**: la transmisión sólo baja
la SpO2.

| Caso | SpO2 base (60) | delta real (60) | caída de PaO2 admisible | `f` admisible | `R` equivalente |
|---|---|---|---|---|---|
| `opioid_35m` | 80,000 % | +24,2104 mmHg | 1,8346 mmHg | **(0, 0,075776]** | ≥ 13,1968 |
| `opioid_67f` | 84,000 % | +21,4034 mmHg | 6,2378 mmHg | (0, 0,291441] | ≥ 3,4312 |

La región **común** es la intersección: `f ∈ (0, 0,075776]`, atada por `opioid_35m`. **No es un punto, no se
elige punto medio y el centro no es preferido.** A transmisión completa (R = 0,8) la SpO2(60) cae a 25,2492 %
y 37,2165 %: el colapso que la docencia rechazó, ahora con su mecanismo.

## 4 · El hallazgo que cambia la pregunta

**El objetivo docente ya se cumple con el enlace apagado — en nivel, no en trayectoria.** La SpO2(60) vale
80,0 % y 84,0 %: las dos dentro de [78, 88]. Y es **plana**, `SpO2(1) == SpO2(60)` exactamente, mientras la FR
cae de 5,970 a 4,442 y de 7,960 a 5,922.

El razonamiento docente —una hipoventilación grave debe crear hipoxemia importante— ya está honrado por la
SpO2 de llegada redactada. Lo que **no** lo produce es el mecanismo: una ventilación que empeora no mueve la
oxigenación. Eso, y no el nivel, es lo que falta.

## 5 · Veredicto de P3-117 y por qué P3-118 no se ejecutó

**`C · EXISTING_INTERFACE_CANNOT_EXPRESS_PARTIAL_TRANSMISSION`**, con consecuencia
**`D · FROZEN_COMMON_CORE_EXTENSION_REQUIRED`: STOP.**

La región existe y preserva asma. Lo que no existe es una interfaz honesta para expresarla: el único mando
que escala la transmisión significa otra cosa, y afirmar R = 13,1968 sería ajustar un número contra una
cantidad declarada. Una transmisión parcial honesta necesita un **coeficiente de transmisión propio** —un
parámetro nuevo y una ecuación modificada en `clinical_core/`— y la regla arquitectónica del encargo convierte
eso en STOP. P3-118 estaba condicionado a que una interfaz certificada existente alcanzara: no alcanza.

**El falsificador docente no se dispara.** Preveía que *ninguna* región común satisficiera la conducta. La
satisface. Decir `COMMON_SINGLE_FACTOR_INSUFFICIENT` ocultaría una región medida que la docencia puede querer
autorizar, así que se informa lo que se midió y se para el mecanismo igual.

### El lazo indirecto que el invariante no vigila

P2T-5 rechaza el impulso hipoxémico por ser «un lazo que ninguna auditoría ha examinado» y a la vez **exige**
el impulso ácido. Medido en `opioid_35m` a R = 0,8: el PaCO2(60) de la propia corrida baja de 93,2104 a
90,5026, la FR sube de 4,4416 a 4,5745 y la entrega relativa cae de 1,0 a 0,3051. La letra de la documentación
se sostiene —no hay escritura directa de vuelta— pero el enlace **no es el mapa de una sola vía** que sugiere:
el camino es SpO2 → déficit / carga ácida → impulso respiratorio → FR → W → PaCO2 → SpO2. Es continuo, no un
umbral: la consciencia vale 2,0 en todo el barrido y el desvío crece de forma monótona con la transmisión.

### Asma (P3-120), sin ajustar nada aparte

| Caso | sin enlace | en el borde común | desplazamiento | a transmisión completa | clasificación |
|---|---|---|---|---|---|
| `asthma_49m` | 89,000 % | 88,6072 % | **−0,3928** | 79,6511 % (−9,35) | `ASTHMA_COMPATIBLE` |
| `asthma_24f` | 90,000 % | 89,6260 % | **−0,3740** | 80,8834 % (−9,12) | `ASTHMA_COMPATIBLE` |

Siempre a la baja, que es la dirección correcta. **Limitación declarada:** la envolvente certificada de asma
no se re-corrió, porque la región no se habilita.

### Las cuatro monotonías de P2T-5: las cuatro se cumplen

Más PaCO2 nunca sube la SpO2; menos nunca la baja, con igualdad **exacta** en delta = 0; peor G y menos FiO2
nunca la suben, por la monotonía estricta del enlace en `SpO2_base`, que es la vía por la que G y FiO2 entran.

## 6 · Lo que se auditó alrededor

**P3-119 / P3-121 — causalidad del manejo opioide.** Matriz de seis vías, 90 minutos, 0 huecos: el oxígeno
sube la SpO2 (80,00 → 85,70) y no toca la FR; la naloxona sube la FR (4,788 → 14,691 al minuto 45, monótona,
sin paradoja) y no toca la SpO2; juntos son la unión exacta; esperar cuesta ventilación **en la integral**
(848,95 contra 1107,01) y casi converge en el extremo, porque la naloxona es persistente; sin tratar, el PaCO2
sube de forma sostenida. **No** se declara `OPIOID_MANAGEMENT_CAUSALITY_READY`: la distinción clínica esencial
—que la naloxona corrige la oxigenación *corrigiendo la ventilación*— es justo el eslabón que §5 deja sin
implementar. Lo demostrable hoy es la mitad.

**P3-122 — ACS en vivo: auditado y rechazado.** La semántica de acciones alcanza; el **mapeo de llegada** no.
`AcsIschaemiaAdapter.anchors()` ignora `state` y devuelve una llegada de referencia fija, donde el adaptador
de GI mapea la que recibe; en vivo, la sombra calcularía un paciente de referencia y lo etiquetaría como este
paciente. Y el motor redacta más variantes de ACS que el único caso declarado. `LIVE_FAMILIES` sigue siendo
`('gi_bleed',)`. Declarado en `runtime_shadow_families.ACS_LIVE_GAP`.

De paso se corrigió un **defecto propio de `0aee3b3`**: el docstring afirmaba que `reperfusion_referral` era
`NOT_PHYSIOLOGICAL` y no lo es, así que el pedido registraba un hueco falso aunque la reperfusión estuviera
representada. Ahora es hueco sólo cuando el motor no cronometró reperfusión, y el replay reproduce el camino
vivo dígito a dígito, incluida ella.

**P3-123 — edema: corrección parcial de FD-P3-100.** No falta contrato compartido:
`DecongestiveTreatment(id, begins_at_minute)` ya existe como contribuidor registrado de tipo `INTERVENTION`
con la **misma forma** que `NaloxoneReversal` y `CoronaryReperfusion`, y `EdemaCongestion` lee su señal con
`heard(...)`. La señal ya es de tiempo de tratamiento. Lo que sigue bloqueado es la **magnitud**: vive en
`decongestion_per_min`, un parámetro de construcción que vale 0,0 por omisión, y la única tasa del repositorio
está declarada `SYNTHETIC_ONLY` con «no magnitude is authored». Veredicto:
`EDEMA_DECONGESTION_MECHANISM_READY_MAGNITUDE_NOT_AUTHORED` — **STOP por falta de un número docente, no por
arquitectura**. Es la puerta más cercana a una quinta familia causal: una sola cifra la abre.

**P3-124 — barrido multifamiliar.** Las seis familias abren y corren el horizonte completo de 120 minutos sin
fallos, y todo hueco que aparece está entre los declarados por su adaptador.

## 7 · Lo que este ciclo NO hizo

No encendió el enlace en ningún perfil comprometido; no adoptó parámetro alguno; no tocó `clinical_core/`; no
dio autoridad en tiempo de ejecución; no cambió lo que ve el residente; no ajustó curvas al legado; no re-corrió
la envolvente certificada de asma; y no llamó verdad clínica a ninguna medición de aquí.
