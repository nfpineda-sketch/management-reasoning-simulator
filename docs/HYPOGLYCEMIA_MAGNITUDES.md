# Hipoglicemia — magnitudes implementadas

> **Estado: IMPLEMENTADO y REVISADO** en `glucose_rescue.py`, `clinical_cases.py` (tres variantes) y la rama `hypoglycemia` de `family_engine.py`, con las decisiones docentes del 2026-09-20 y la revisión de magnitudes del mismo día (rebote por sobrecorrección). Son parámetros docentes, no un modelo predictivo. Las trayectorias de abajo salen del motor ya implementado. Las demás familias del banco, PS001 y los casos generados dan exactamente lo mismo que antes.

## Decisión docente

La facultad aprobó agregar todo lo que faltaba junto a la ampolla de glucosa: octreótido como tratamiento específico de la hipoglicemia por sulfonilurea, glucagón intramuscular cuando no hay vía, carbohidrato oral en el paciente despierto, glucosado al 10% en infusión, tiamina donde importa, y una consecuencia para la neuroglucopenia que se deja demasiado tiempo.

## Las tres variantes

| Caso | Llegada | Glucosa | Declaración |
|---|---|---|---|
| **28m, diabetes tipo 1** | 128/76 · FC 112 · somnoliento | 34 | insulina, sin recurrencia |
| **76f, sulfonilurea** | 134/78 · FC 96 · obnubilada | 38 | `recurrence_risk`, la glucosa vuelve a caer |
| **54m, alcohol y ayuno** | 118/70 · FC 104 · somnoliento, mirada inestable | 32 | `thiamine_deficient` |

El 54m es nuevo: lo trae el personal de un albergue, bebe a diario y casi no ha comido en una semana. El examen neurológico describe nistagmo y marcha no evaluable.

## Magnitudes implementadas

| Mecanismo | Magnitud |
|---|---|
| Caída espontánea | −0.08 mg/dL por minuto; **−0.6 con sulfonilurea** |
| Dextrosa IV | +4 mg/dL por gramo, hasta 10 g por minuto |
| **Octreótido** | 25 a 500 mcg. Desde los 15 min y por 6 h, devuelve la caída a −0.08 |
| **Glucagón** | +1.6 mg/dL por minuto, desde los 10 min y por 25 min. Segunda dosis: la mitad. Tercera: nada |
| **Carbohidrato oral** | +1.2 mg/dL por minuto, desde los 5 min y por 25 min. **Solo con el paciente alerta** |
| **Glucosado 10%** | 0.1 g por mL: 400 mL/h son 0.67 g/min |
| **Convulsión** | Bajo 40 mg/dL durante 20 min; 10 min post-ictal |
| **Rebote por sobrecorrección** | Sobre 200 mg/dL en un paciente con páncreas funcionando: a los 30 min la glucosa cae **0.8 mg/dL/min extra**, hasta bajar de 100. La hiperglicemia en sí no se castiga, porque sobre 300 tiene poca repercusión aguda |
| **Encefalopatía de Wernicke** | Si la glucosa se da sin tiamina dentro de 30 min, en un caso depletado |
| Reversión con tiamina | Constante de 30 min |
| Estado mental por glucosa | ≥ 70 alerta, ≥ 45 somnoliento, ≥ 25 obnubilado, bajo eso sin respuesta |
| FC al recuperarse | Baja 18 latidos desde el basal cuando la glucosa pasa de 70 |

## Trayectorias del motor

### 28m, insulina

| Escenario | 20–25 min | 40 min | 60–70 min |
|---|---|---|---|
| Sin tratar | **convulsión** a los 20 min; glucosa 32, sin respuesta | glucosa 31, obnubilado | — |
| Dextrosa 25 g | 10′: glucosa **133**, alerta, FC 112 → 94 | — | glucosa 129, alerta |
| Glucagón 1 mg IM | glucosa 50, **somnoliento todavía** | glucosa 72, alerta | glucosa 70, alerta |

El glucagón tarda el doble y llega a la mitad: a los 20 minutos el paciente sigue somnoliento, cuando con la ampolla ya estaba alerta a los 10.

### 76f, sulfonilurea

| Escenario | 20 min | 60 min | 100 min |
|---|---|---|---|
| Solo dextrosa | 126 | 102 | **78** (recae) |
| **Dextrosa y octreótido** | 129 | 126 | **123** |
| Dextrosa y glucosado 10% a 400 mL/h | 40′: 221 | 80′: **303** | — |

La infusión a 400 mL/h corrige de más y ahora eso tiene consecuencia: pasado 200 mg/dL, el páncreas de esta paciente responde y la glucosa vuelve a caer, 0.8 mg/dL por minuto además de su propia recurrencia.

### Sobrecorrección: el rebote

Con 50 g de dextrosa en el hombre de 54 años, que no es diabético:

| min | Glucosa | Evento |
|---|---|---|
| 10 | 231 | **"The correction overshot…"**: el páncreas responde |
| 60 | 206 | cayendo |
| 120 | 154 | cayendo |
| 180 | **101** | de vuelta al punto de partida |

Con 25 g la glucosa llega a 131 y se queda ahí. En el hombre de 28 años con diabetes tipo 1, los mismos 50 g no producen rebote: no hay páncreas que responda.

### 54m, depletado de tiamina

| Escenario | 20 min | 40–60 min | 110 min |
|---|---|---|---|
| **Glucosa sola** | glucosa 130, **confuso** | glucosa 127, confuso | sigue confuso |
| Tiamina junto con la glucosa | glucosa 130, **alerta** | glucosa 127, alerta | — |
| Tiamina como rescate a los 40 min | 40′: confuso | 70′: confuso | **alerta** |

El aviso dice: "Confusion persists with nystagmus and an unsteady gaze although the glucose is now normal: glucose was given to a thiamine-depleted brain. Thiamine is the missing treatment."

## Qué más cambió

- **Órdenes nuevas** en los dos idiomas: octreótido, glucagón, tiamina, carbohidrato oral, glucosado al 10% en infusión.
- **El carbohidrato oral se rechaza** con una aclaración cuando el paciente no está alerta, en vez de ejecutarse.
- **El imperativo informal en español** ("dale") ya se reconoce.
- Los tres medicamentos nuevos quedaron disponibles también para los casos generados, por el contrato de capacidades.

## Fuera de este cambio

- **Hipoglicemia por insulina exógena facticia, insulinoma e insuficiencia suprarrenal.**
- **El número de la hiperglicemia**: sobre 300 mg/dL no tiene repercusión aguda modelada, por decisión docente. Lo que se modela es el rebote que provoca.
- **Potasio** con la infusión de glucosa e insulina.
- **Destino y observación prolongada** de la sulfonilurea, más allá del encuentro.
- **Los casos generados por IA** no tienen nada de este bloque.
