# Intoxicación por opioides — magnitudes implementadas

> **Estado: IMPLEMENTADO** en `opioid_reversal.py` y la rama `opioid` de `family_engine.py`, con las decisiones docentes del 2026-09-20. Son parámetros docentes, no un modelo predictivo. Las trayectorias de abajo salen del motor ya implementado. Las demás familias del banco, PS001 y los casos generados dan exactamente lo mismo que antes.

Aplica a `opioid_35m` (106/64, FC 68, SpO₂ 80%, FR 6, obnubilado, exposición incierta a un comprimido) y `opioid_67f` (104/62, FC 62, SpO₂ 84%, FR 8, obnubilada, opioide de acción prolongada).

## Decisión docente

La facultad aprobó las tres piezas que faltaban: un opioide de acción prolongada que sobreviva al antídoto, de modo que los bolos aislados no basten y la infusión sea el tratamiento; abstinencia cuando la naloxona se empuja más allá de lo que la ventilación necesita; y un desenlace para la apnea que nadie soporta.

## Magnitudes implementadas

| Mecanismo | Magnitud |
|---|---|
| Opioide de acción corta | Decae 0.1% por minuto: vida media de unas 11 h |
| **Opioide de acción prolongada** | Decae 0.03% por minuto: sobrevive al encuentro |
| Naloxona | Decae 2.5% por minuto: vida media de 27 min |
| Dosis | 0.4 mg IV equivale a **una unidad** de antídoto; ya no hay tope en 1.4 |
| **Infusión de naloxona** | 2.5 unidades por mg/h: 0.4 mg/h sostiene un nivel de 1.0 |
| **Abstinencia** | Sobre 1.2 unidades. FC +25, PAS +20, FR +6 por unidad de exceso, hasta 1.5 |
| Depresión respiratoria | FR = 14 − (14 − FR basal) × supresión, con supresión = opioide − naloxona |
| SpO₂ | 97 − (97 − SpO₂ basal) × supresión |
| **Paro respiratorio** | 20 min con FR ≤ 6 o SpO₂ < 80 **sin soporte**; asistolia y estado terminal |
| Ventilación con bolsa-mascarilla | SpO₂ 96, FR 12, y detiene el reloj de la apnea |

## Trayectorias del motor

Anotaciones: PA · FC · SpO₂ · FR · estado mental · nivel de naloxona.

### 35m, acción corta

| Escenario | 5 min | 25–30 min | 60 min |
|---|---|---|---|
| **Sin soporte** | — | 25′: **0/0 · 0 · 0 · 0 · paro**, asistolia | — |
| Solo bolsa-mascarilla | — | 106/64 · 68 · **99** · 12 · obnubilado | — |
| **0.4 mg titulado, con bolsa-mascarilla** | 99 · 12 · **alerta** · nalox 0.88 | 99 · 12 · somnoliento · nalox 0.47 | 99 · 12 · **obnubilado** · nalox 0.22 |
| **2 mg de golpe** | **136/82 · 106 · 23 · agitado** · nalox 4.41 | 129/78 · 96 · 21 · agitado | 106/64 · 68 · 14 · alerta |

Los dos errores quedan a la vista. Ventilar sin antídoto mantiene vivo al paciente pero obnubilado. Dar el antídoto y no vigilar deja que la renarcotización lo devuelva a obnubilado en una hora, porque la naloxona se va antes que el opioide.

### 67f, acción prolongada

| Escenario | 30 min | 60 min | 90 min |
|---|---|---|---|
| **Solo bolos** | 90 · 11 · somnolienta · nalox 0.47 | **87 · 9 · obnubilada** · nalox 0.22 | 86 · 9 · obnubilada · nalox 0.10 |
| **Bolo más infusión 0.4 mg/h** | **97 · 14 · alerta** · nalox 0.97 | — | **97 · 14 · alerta** · nalox 0.97 |

Es el contraste central de la familia: el mismo bolo inicial, y a los 90 minutos una paciente obnubilada con SpO₂ 86 o una despierta con 97.

## Qué más cambió

- **Orden nueva:** infusión de naloxona, en los dos idiomas, con tasa en mg/h o mcg/h, y se puede suspender.
- **La dosis de naloxona ya no está topada.** Antes cualquier dosis sobre 0.56 mg daba lo mismo, así que el exceso no podía enseñarse.
- **El flag de recurrencia del caso**, que ya existía, ahora hace algo en esta familia: define el decaimiento del opioide.
- **El estado terminal** es el mismo que usan la fibrilación del SCA y PS001: la reevaluación ordinaria se detiene y el manejo del paro queda fuera del build.

## Fuera de este cambio

- **Manejo del paro:** compresiones, adrenalina y desfibrilación no son ejecutables.
- **Intubación como alternativa a la bolsa-mascarilla**: funciona, pero no se modela distinto.
- **Edema pulmonar por naloxona**, rabdomiólisis, aspiración y lesión por presión.
- **Coingestas**, buprenorfina y opioides sintéticos que requieren dosis mayores.
- **Los casos generados por IA** no tienen nada de este bloque.
