# Enmienda 3 · Tono vascular común: soporte vasoconstrictor y primer escritor · registro (2026-11-17)

**Estado: CANDIDATA (la certificación se registra en el commit de promoción; el estado vigente es siempre el de `PHASE2_AMENDMENT_3.json`).** Sucesor formal de `PHASE2_AMENDMENT_2`, sólo en sombra: apagado por omisión
(`CoreProfile.vasoconstrictor_support_to_tone_gain = None`), sin autoridad en tiempo de ejecución, invisible para el residente y
ausente de la puntuación. **No hay afirmación de validación clínica ni de dosis-respuesta:** toda magnitud es una
`DEVELOPMENT_BEHAVIOURAL_REGION` con tres testigos de prueba (`LOW`, `CENTER_REFERENCE`, `HIGH`), ninguno elegido.

Digesto del núcleo enmendado: `867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c` (146 fuentes). Predecesores, reconstruidos exactos desde los archivos vivos:
Enmienda 2 `a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2` (144 fuentes), Enmienda 1
`10b45ce2967ea55afccb35291afb5bb1f7f1b01eb4a253e6a0736c02a5878635` (142 fuentes) y cierre de la Fase 2
`22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a` (141 fuentes). Registro ligado: `PHASE2_AMENDMENT_3.json`.
Autorización: decisiones docentes FD-TONE-01 a FD-TONE-12 (2026-11-17). Rama: `phase-3-runtime-integration`.

## 1 · Qué agrega
| Decisión docente | Implementación |
|---|---|
| El tono es un estado **general**; la norepinefrina no es el tono (FD-TONE-01) | El canal `T` no cambia y conserva un único escritor, la respuesta de tono del núcleo. Lo nuevo es una **entrada** de su objetivo: `objetivo = C(s) × B(b) × K(u)`, `K(u) = 1 + k·u/(1 + u)`. |
| La norepinefrina es el **primer** escritor; otros caben sin ecuaciones por fármaco (FD-TONE-02) | `aux.vasoconstrictor_support` (`u`) es común; todo escritor suma un `VasoconstrictionChange`. `vascular_support.Norepinephrine` es el único escritor que existe. |
| `T` no rescata un flujo ausente (FD-TONE-04) | Nada nuevo: la presión es gasto × tono, y `derive` no reporta presión, gasto ni entrega sin pulso. |
| `T` no agrega volumen (FD-TONE-05) | Contrato del escritor: no escribe `V`, hemoglobina ni bomba. Probado minuto a minuto. |
| Sin calibración ni objetivo en mmHg (FD-TONE-06) | Región amplia con evidencia, supuesto, incertidumbre, confianza (< 0,80 en todas) y falsador; ningún punto elegido. |

## 2 · Inserciones declaradas (reversibles y probadas)
| Archivo común | Inserciones | Qué |
|---|---|---|
| `clinical_core/provenance.py` | 5 | `VasoconstrictionChange`; `MinuteRecord.vasoconstriction` (serializado sólo si no está vacío). |
| `clinical_core/state.py` | 4 | `AuxiliaryState.vasoconstrictor_support` (`None` = no se registra; ausente del estado serializado). |
| `clinical_core/derived.py` | 5 | El campo del perfil, su entrada `PROVISIONAL` en el registro de parámetros y el factor `K` en `tone_target`. |
| `clinical_core/integration.py` | 18 | `Contribution.vasoconstriction`, la suma del minuto (con el rechazo de un soporte que ya viene en el estado bajo un lector sin declarar y de una suma no finita), el invariante de conservación del minuto, la comprobación de propiedad, el factor `1 + k` en el dominio del tono y el texto de los rechazos de la guarda y del lazo (sin cambio mientras el lector esté sin declarar). |
| `clinical_core/decision_pack.py` | 1 | La etapa queda fuera del digesto del paquete de decisiones, como las anteriores. |

Archivos nuevos: `clinical_core/vascular_support.py` (el factor, la región, los testigos, la rejilla de los escritores
—aportes en múltiplos de 2⁻⁴⁰ y soporte estacionario por debajo de 2¹⁰ semiefectos, para que el estado sea **exactamente** la
suma de sus escritores en cada minuto— y el escritor) y
`clinical_core/amendment_3.py` (la etapa formal: reversión declarada, pruebas de la reversión, vistas del árbol de cada
predecesor para sus propias pruebas).

## 3 · Región de desarrollo (no es una calibración)
| Magnitud | Cotas | Confianza | `LOW` | `CENTER_REFERENCE` | `HIGH` |
|---|---|---|---|---|---|
| `tone_gain` (`k`) | 0,3 – 0,9 | 0,5 | 0,3 | 0,6 | 0,9 |
| `half_effect_rate_mcg_min` | 5 – 20 | 0,5 | 20 | 10 | 5 |
| `onset_tau_min` | 0,5 – 3,0 | 0,7 | 3,0 | 1,5 | 0,5 |
| `offset_tau_min` | 1,0 – 5,0 | 0,6 | 1,0 | 2,5 | 5,0 |

La cota superior de `k` es la del propio núcleo: con la mayor compensación comprometida (1,5) una ganancia de 1,0 pone el mayor
objetivo alcanzable sobre la guarda de `T` (3,0), y el dominio del tono lo rechaza antes de ejecutar.

## 4 · Apagada por omisión
Con el lector sin declarar: el perfil serializado, el estado serializado, el registro de cada minuto y el digesto de toda
trayectoria comprometida son los que eran; un escritor del soporte se **rechaza** (nada lo leería), nunca queda inerte en
silencio. Declarar el lector sin escritor registra un soporte de 0 y no cambia ninguna lectura.

## 5 · Qué no se afirma
- Ni calibración clínica ni dosis-respuesta; ningún objetivo en mmHg; sin motor de titulación, sin dosis por peso, sin segundo
  fármaco vasoactivo.
- Sin autoridad en tiempo de ejecución, sin cambio visible para el residente y sin efecto en la puntuación: la autoridad viva
  de presión de GI **no** acepta la norepinefrina.
- El soporte no crea volumen ni gasto de bomba; la semántica dura de «sin pulso» no cambia.
- El núcleo común no termina un encuentro.

## 6 · Certificación
Pendiente en este commit: la certificación del candidato se registra en el commit de promoción.
