# P2I-2P · Fisiología de la entrega y la extracción de O2: revisión y corrección estructural

Este paquete trabaja sólo en sombra. No aprueba ningún valor numérico, no cambia lo que ve el residente, no migra GI ni
otra familia y no vuelve a filtrar el lactato. Los resultados de P2I-2R quedan **PENDIENTES DE REFILTRADO** tal como se
comprometieron (`docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md`).

Contenido:
- la auditoría de lo que significaban «entrega», «demanda» y el umbral 1 (§1);
- el defecto conceptual (§2);
- la corrección implementada, con un parámetro nuevo, `oxygen_extraction_reserve`, PROVISIONAL y TBD (§3);
- las sondas sintéticas A–J y la revisión de los tres hallazgos de P2I-2R (§4–§7);
- recomendaciones sobre la interfaz con el colapso y la lectura de FD-LAC-01/06 (§8–§9);
- lo que sigue TBD (§10).

La reserva canónica queda en 1, el modelo previo. Por eso ninguna cifra canónica cambia: el golden GI sólo gana la entrada
de metadatos del parámetro nuevo (§11).

## 0. Decisión docente FD-LAC-06 (registrada, todavía no operacionalizada)

Texto original de la docencia (2026-10-27), citado tal cual:

> A delivery state that is still below the current adequacy threshold BUT is clearly recovering during active
> resuscitation must NOT automatically be classified as "persistent/worsening inadequate delivery."
>
> PERSISTENT/WORSENING inadequate delivery: delivery remains inadequate through the clinically meaningful reassessment
> interval; AND there is no meaningful recovery trend, or delivery worsens.
>
> RECOVERING-BUT-STILL-SUBTHRESHOLD delivery: delivery remains below the adequacy boundary; BUT delivery improves over
> the reassessment interval during effective resuscitation.
>
> In the second state, lactate may plausibly decline because production is falling and accumulated lactate is being
> cleared. Therefore FD-LAC-06 must not reject a lactate fall solely because delivery has not yet crossed a binary
> threshold. Do NOT introduce a 5% tolerance as an approved faculty constant. For a deterministic/noise-free model,
> initially use trajectory direction and state transition semantics rather than inventing a percentage threshold.
> Do not refilter yet.

En este paquete no se codifica en `faculty_constraints.py` ni se vuelve a filtrar. La propuesta de cómo leerla con el
estado de oxigenación corregido está en §9.

**2026-10-27:** la docencia aceptó P2I-2P y decidió la semántica, los estados, la lectura de FD-LAC-06 y la banda candidata
de ρ (2,0–3,0). El registro está en `docs/revision/P2I2Q_PLAUSIBILIDAD_HEMODINAMICA.md` §0.

## 1. Auditoría de terminología y dimensiones (P2I-2P-1)

Estado anterior a P2I-2P, inferido del código y de su documentación, sin suponer:

| Término | Definición | Unidades | Interpretación implícita | ¿Consistente? |
|---|---|---|---|---|
| Entrega relativa `delivery_rel` | (Q/Q₀)·(Hb/Hb₀)·(SpO2/SpO2₀), con 0 = la llegada | adimensional, relativa a la llegada del propio paciente | DO2(t)/DO2(llegada); omite el O2 disuelto | Sí |
| `arrival_delivery_ratio` | ancla del caso; banda GI 0,6–1,0 (punto medio 0,85); 1 neutro | «unidades de la entrega que satisface la demanda de referencia» | En GI, la entrega de llegada respecto de la **mínima adecuada** (B): «en o bajo la adecuación; 1 es una llegada compensada, 0,6 un déficit grave en curso». En la llegada neutra sana (1), la **normal** (C) | No: B y C coinciden sólo sin reserva de extracción |
| Entrega efectiva `effective_delivery` | `arrival_delivery_ratio` × `delivery_rel` | las de la fila anterior | la misma ambigüedad B/C | Hereda la ambigüedad |
| Demanda `oxygen_demand` | `metabolic_demand_baseline` × modificadores declarados (P2E-2) | «unidades de la entrega que la satisface»; 1 neutro, más de 1 sólo con evidencia hipermetabólica | Por su definición, el consumo metabólico de O2 relativo al normal (A, VO2) | No: es un VO2 medido en unidades de entrega. Igualar 1 de demanda a 1 de entrega supone que la entrega normal se consume entera |
| Déficit `delivery_deficit` | máx(0, demanda − entrega) | unidades de entrega | la demanda no cubierta | Sólo si la entrega normal ya fuera la crítica. Con reserva de extracción, una entrega un 30 % menor no deja demanda sin cubrir |
| D | dD/dt = g·déficit − D/τ_D; D(0) = `arrival_oxygen_debt` | índice·min | la deuda de O2 acumulada y repagable | Como integrador sí; hereda el déficit |
| Umbral 1,0 | entrega = demanda | — | Es la entrega **crítica** (B) en el tope de la banda GI y en la definición confirmada de FD-LAC («inadequate delivery = oxygen delivery < oxygen demand», `adequate()`). Es la **normal** (C) en la llegada neutra y en las sondas P2F-6 (una anemia aislada del 40 % desde lo normal acumula deuda) | Ambiguo |

**Respuesta explícita: ¿qué significa «demanda»?**
- **Por definición, A:** el consumo o la demanda metabólica de O2 relativa a la normal, escalada por modificadores
  metabólicos. Ningún texto define la demanda como una entrega.
- **Pero su unidad se usó como B y como C.** Se expresa en «unidades de la entrega que la satisface»:
  - como B, la mínima adecuada: banda GI y FD-LAC;
  - como C, la normal: llegada neutra y P2F-6.
- **Por eso, en el modelo tal como funcionaba, la respuesta honesta es D:** un VO2 (A) medido en una unidad de entrega
  ambigua entre B y C, que sólo coinciden sin reserva.
- La ambigüedad no se elige en silencio: se resuelve en §3 con dos índices separados y una reserva explícita.

## 2. Defecto conceptual

- **Falta la reserva de extracción.** Sin ella, la entrega normal (C) y la crítica (B) son la misma. Equivale a suponer
  que en reposo la extracción ya es máxima: 1 de entrega se «consume» entera, una igualdad DO2 = VO2 implícita.
- **Consecuencias:**
  - toda entrega por debajo de lo normal genera deuda. Con reserva 1, las sondas B (gasto −30 %), D (anemia) y G
    (demanda × 1,5) acumulan D y suben el lactato (§4.1);
  - no existe un estado compensado: un índice mayor que 1 se lee como «exceso» (hallazgo 3), y uno menor que 1 siempre
    como deuda.
- **La misma unidad cumple dos papeles:** es la crítica (B) en GI y en FD-LAC, y la normal (C) en la llegada neutra y en
  P2F-6. Sólo es coherente con reserva 1.

## 3. Modelo corregido (P2I-2P-2, implementado en sombra)

| Magnitud | Definición | Dónde |
|---|---|---|
| Índice de entrega (DO2) | DO2 / DO2 normal en reposo = `arrival_delivery_ratio` × (Q/Q₀)(Hb/Hb₀)(SpO2/SpO2₀) | `derived.effective_delivery` (mismo cálculo, unidad aclarada) |
| Índice de demanda (VO2) | VO2 demandado / VO2 normal en reposo = `metabolic_demand_baseline` × modificadores | `derived.oxygen_demand` (sin cambios de cálculo) |
| Relación de suministro | índice de entrega / índice de demanda (1 = extracción normal) | `derived.oxygen_balance` |
| Reserva de extracción ρ | E_máx / E_normal | `CoreProfile.oxygen_extraction_reserve`: PROVISIONAL, TBD, canónica 1, nunca < 1 |
| Extracción requerida | 1 / relación de suministro, relativa a la normal | `OxygenBalance.required_extraction` |
| Entrega crítica | demanda / ρ | `OxygenBalance.critical_delivery` |
| Déficit efectivo | máx(0, demanda − ρ × entrega): la demanda que queda sin cubrir con la extracción agotada, en unidades de VO2 normal | `derived.effective_oxygen_deficit` |
| Estado | ADEQUATE si la relación es ≥ 1; COMPENSATED si 1/ρ ≤ relación < 1; CRITICAL si relación < 1/ρ | `derived.oxygen_balance` |

- **D:** dD/dt = g·déficit efectivo − D/τ_D (`integration._oxygen_debt`).
  - D integra **sólo** el déficit efectivo. La entrega por encima de la crítica no acumula deuda ni da crédito.
  - D nunca baja de 0 y sigue siendo una deuda repagable, distinta del lactato. El lactato sigue leyendo D
    (X' = k·D − X/τ_L) y conserva su propia dinámica: retraso, disociación transitoria y elevación después de restituir.
- **Forma de la curva:**
  - es la bifásica clásica, reducida al mínimo: el consumo es independiente del suministro hasta la entrega crítica, y por
    debajo depende de él (VO2 = ρ·DO2);
  - la curvatura cerca del punto crítico es TBD; no se modeló la microcirculación.
- **Neutralidad:** con ρ = 1 el déficit efectivo es exactamente el déficit previo; una prueba lo verifica. Como la
  reserva canónica sigue en 1, ninguna trayectoria canónica cambia.
- **Identificabilidad:** el déficit efectivo es máx(0, demanda − ρ × `arrival_delivery_ratio` × `delivery_rel`), así que
  a D y al lactato sólo llega el **producto** ρ × `arrival_delivery_ratio`. Dos lecturas de la banda GI ante una reserva
  ρ > 1, comprobadas en §4.2–§4.5 sobre los mismos candidatos:
  - **banda fija:** el valor se lee como DO2 sobre lo normal (C). La dinámica cambia:
    - toda llegada GI pasa a estar compensada, contra el diseño de la banda («0,6 un déficit grave en curso»);
    - D se repaga sin tratar, y el lactato L1 de los 60 min cae por debajo del de llegada con sangrado activo. Queda
      fuera de la envolvente docente de FD-LAC-02/03, cuyo límite inferior es el lactato de llegada (§6).
    - No es FD-LAC-01 la que lo detecta: leída como CRITICAL (§9), la ventana pasa a compensada y FD-LAC-01 no aplica;
  - **banda re-anclada:** se lee como fue diseñada, en unidades de la entrega crítica (B), y el índice sobre lo normal es
    relación / ρ. D y el lactato quedan **idénticos** a los canónicos (diferencia máxima < 1e-14).
    - Cambian los estados y los índices, que pasan a significar lo que dicen.
    - También cambian dos lectores que comparan la entrega con la demanda sin la reserva:
      - la bandera del recorte «sin crédito» de `shadow.acting_mechanisms`, ya corregida a ρ × entrega > demanda;
      - `faculty_constraints.adequate`, la definición congelada de FD-LAC, que no se tocó (§9).
    - Con ρ = 1, ninguno de los dos cambia.
- **Guarda:** `lactate_slice.slice_run` rehúsa una reserva distinta de 1 si no se declara explícitamente la
  `arrival_delivery_ratio`, es decir, la lectura de la banda. Ninguna corrida GI aplica la banda fija en silencio. El
  registro de calibración no incluye la reserva, así que ningún candidato la fija.
- **Coherencia de la lectura re-anclada (orientación aritmética, no aprobación):**
  - con ρ entre 2 y 3, la banda 0,6–1,0 da un DO2 de llegada de 0,2–0,5 de lo normal;
  - una Hb de 6,7 g/dL es cerca de 0,45–0,5 de una Hb normal de 13–15 g/dL; es un supuesto, porque el caso no declara
    la Hb habitual. Multiplicada por un gasto reducido, da 0,3–0,45;
  - la banda fija (0,6–1,0 de lo normal con la Hb a la mitad) exigiría un gasto normal o supranormal en un paciente en
    shock.
- **No se tocó:**
  - las bandas, el registro de calibración y su congelamiento (`152abc6c…`);
  - `gi_reference.py` y `calibration.py`: el texto de unidad de la banda, «la entrega que satisface la demanda de
    referencia», es B y sigue congelado;
  - las sondas P2F-6;
  - las reglas FD-LAC.

## 4. Sondas y hallazgos (generado)

<!-- generado:oxigeno -->
Generado desde las sondas `760627b365b161b166872b932b2bd5cf4fdba6b3507ad17a28215dfb2a8f1357` (`python -m clinical_core.oxygen_probes`). Reserva canónica 1 (neutra: el modelo previo); reserva ilustrativa 2,5, sintética y no propuesta. Colapso: sólo un cálculo sobre cada trayectoria, con un umbral de gasto sintético de 0,3 y un límite de carga sintético de 30 minutos a severidad plena; la regla del núcleo sigue apagada. Los lactatos de las sondas A–J usan las cinéticas por defecto del perfil (TBD): importa su dirección, no su magnitud.

### 4.1 Sondas A–J

Índice de entrega (DO2 / DO2 normal en reposo), índice de demanda (VO2 demandado / VO2 normal en reposo), estado de oxigenación, extracción requerida (relativa a la normal), déficit efectivo (lo que D integra), D, lactato y las dos cargas de colapso sintéticas (gasto / déficit de O2).

**A · normal** — entrega y demanda normales.

| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | Carga gasto | Carga déficit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 15 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 30 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 60 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 90 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 120 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 15 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 30 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 60 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 90 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 120 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |

| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | Límite de colapso sintético alcanzado (gasto / déficit) |
|---|---|---|---|---|
| 1 | = = = = = | nunca | 0,0 | no / no |
| 2,5 | = = = = = | nunca | 0,0 | no / no |

**B · entrega baja compensada** — la bomba cae 30 % en 30 min y se mantiene.

| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | Carga gasto | Carga déficit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 15 | 0,85 | 1,00 | crítica | 1,18 | 0,15 | 1,0 | 1,00 | 0,0 | 1,2 |
| 1 | 30 | 0,70 | 1,00 | crítica | 1,43 | 0,30 | 3,7 | 1,02 | 0,0 | 4,7 |
| 1 | 60 | 0,70 | 1,00 | crítica | 1,43 | 0,30 | 9,4 | 1,10 | 0,0 | 13,7 |
| 1 | 90 | 0,70 | 1,00 | crítica | 1,43 | 0,30 | 12,8 | 1,21 | 0,0 | 22,7 |
| 1 | 120 | 0,70 | 1,00 | crítica | 1,43 | 0,30 | 14,9 | 1,31 | 0,0 | 31,7 |
| 2,5 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 15 | 0,85 | 1,00 | compensada | 1,18 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 30 | 0,70 | 1,00 | compensada | 1,43 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 60 | 0,70 | 1,00 | compensada | 1,43 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 90 | 0,70 | 1,00 | compensada | 1,43 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 120 | 0,70 | 1,00 | compensada | 1,43 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |

| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | Límite de colapso sintético alcanzado (gasto / déficit) |
|---|---|---|---|---|
| 1 | ↑ ↑ ↑ ↑ ↑ | 1 | 14,9 | no / 115 |
| 2,5 | = = = = = | nunca | 0,0 | no / no |

**C · entrega que cruza la región crítica** — la bomba cae de forma continua hasta 0,2 en 100 min.

| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | Carga gasto | Carga déficit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 15 | 0,88 | 1,00 | crítica | 1,14 | 0,12 | 0,8 | 1,00 | 0,0 | 1,0 |
| 1 | 30 | 0,76 | 1,00 | crítica | 1,32 | 0,24 | 3,0 | 1,01 | 0,0 | 3,7 |
| 1 | 60 | 0,52 | 1,00 | crítica | 1,92 | 0,48 | 10,5 | 1,10 | 0,0 | 14,6 |
| 1 | 90 | 0,28 | 1,00 | crítica | 3,57 | 0,72 | 20,7 | 1,27 | 0,1 | 32,8 |
| 1 | 120 | 0,20 | 1,00 | crítica | 5,00 | 0,80 | 31,3 | 1,51 | 8,9 | 56,4 |
| 2,5 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 15 | 0,88 | 1,00 | compensada | 1,14 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 30 | 0,76 | 1,00 | compensada | 1,32 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 60 | 0,52 | 1,00 | compensada | 1,92 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 90 | 0,28 | 1,00 | crítica | 3,57 | 0,30 | 2,0 | 1,00 | 0,1 | 2,4 |
| 2,5 | 120 | 0,20 | 1,00 | crítica | 5,00 | 0,50 | 12,4 | 1,10 | 8,9 | 16,5 |

| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | Límite de colapso sintético alcanzado (gasto / déficit) |
|---|---|---|---|---|
| 1 | ↑ ↑ ↑ ↑ ↑ | 1 | 31,3 | no / 87 |
| 2,5 | = = = ↑ ↑ | 75 | 12,4 | no / no |

**D · anemia con gasto conservado** — la Hb baja 0,07 g/dL por min (de 13 a 4,6 g/dL).

| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | Carga gasto | Carga déficit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 15 | 0,92 | 1,00 | crítica | 1,09 | 0,08 | 0,5 | 1,00 | 0,0 | 0,6 |
| 1 | 30 | 0,84 | 1,00 | crítica | 1,19 | 0,16 | 2,0 | 1,01 | 0,0 | 2,5 |
| 1 | 60 | 0,68 | 1,00 | crítica | 1,48 | 0,32 | 7,1 | 1,06 | 0,0 | 9,9 |
| 1 | 90 | 0,52 | 1,00 | crítica | 1,94 | 0,48 | 14,0 | 1,18 | 0,0 | 22,1 |
| 1 | 120 | 0,35 | 1,00 | crítica | 2,83 | 0,65 | 22,0 | 1,35 | 0,0 | 39,1 |
| 2,5 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 15 | 0,92 | 1,00 | compensada | 1,09 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 30 | 0,84 | 1,00 | compensada | 1,19 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 60 | 0,68 | 1,00 | compensada | 1,48 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 90 | 0,52 | 1,00 | compensada | 1,94 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 120 | 0,35 | 1,00 | crítica | 2,83 | 0,12 | 0,4 | 1,00 | 0,0 | 0,6 |

| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | Límite de colapso sintético alcanzado (gasto / déficit) |
|---|---|---|---|---|
| 1 | ↑ ↑ ↑ ↑ ↑ | 1 | 22,0 | no / 106 |
| 2,5 | = = = = ↑ | 112 | 0,4 | no / no |

**E · gasto bajo con Hb conservada** — la bomba cae a 0,3 en 60 min y se mantiene.

| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | Carga gasto | Carga déficit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 15 | 0,82 | 1,00 | crítica | 1,21 | 0,18 | 1,1 | 1,00 | 0,0 | 1,4 |
| 1 | 30 | 0,65 | 1,00 | crítica | 1,54 | 0,35 | 4,4 | 1,02 | 0,0 | 5,4 |
| 1 | 60 | 0,30 | 1,00 | crítica | 3,36 | 0,70 | 15,4 | 1,14 | 0,0 | 21,4 |
| 1 | 90 | 0,30 | 1,00 | crítica | 3,36 | 0,70 | 26,0 | 1,37 | 0,2 | 42,5 |
| 1 | 120 | 0,30 | 1,00 | crítica | 3,36 | 0,70 | 32,4 | 1,61 | 0,4 | 63,5 |
| 2,5 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 15 | 0,82 | 1,00 | compensada | 1,21 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 30 | 0,65 | 1,00 | compensada | 1,54 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 60 | 0,30 | 1,00 | crítica | 3,36 | 0,26 | 1,0 | 1,00 | 0,0 | 1,2 |
| 2,5 | 90 | 0,30 | 1,00 | crítica | 3,36 | 0,26 | 6,6 | 1,06 | 0,2 | 8,9 |
| 2,5 | 120 | 0,30 | 1,00 | crítica | 3,36 | 0,26 | 10,1 | 1,15 | 0,4 | 16,5 |

| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | Límite de colapso sintético alcanzado (gasto / déficit) |
|---|---|---|---|---|
| 1 | ↑ ↑ ↑ ↑ ↑ | 1 | 32,4 | no / 73 |
| 2,5 | = = ↑ ↑ ↑ | 52 | 10,1 | no / no |

**F · gasto bajo y anemia** — bomba a 0,6 y Hb a 7,8 g/dL en 40 min.

| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | Carga gasto | Carga déficit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 15 | 0,72 | 1,00 | crítica | 1,38 | 0,28 | 1,9 | 1,00 | 0,0 | 2,3 |
| 1 | 30 | 0,49 | 1,00 | crítica | 2,04 | 0,51 | 6,7 | 1,03 | 0,0 | 8,4 |
| 1 | 60 | 0,36 | 1,00 | crítica | 2,78 | 0,64 | 18,8 | 1,20 | 0,0 | 27,0 |
| 1 | 90 | 0,36 | 1,00 | crítica | 2,78 | 0,64 | 26,6 | 1,42 | 0,0 | 46,2 |
| 1 | 120 | 0,36 | 1,00 | crítica | 2,78 | 0,64 | 31,3 | 1,64 | 0,0 | 65,4 |
| 2,5 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 15 | 0,72 | 1,00 | compensada | 1,38 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 30 | 0,49 | 1,00 | compensada | 2,04 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 60 | 0,36 | 1,00 | crítica | 2,78 | 0,10 | 1,8 | 1,01 | 0,0 | 2,2 |
| 2,5 | 90 | 0,36 | 1,00 | crítica | 2,78 | 0,10 | 3,5 | 1,04 | 0,0 | 5,2 |
| 2,5 | 120 | 0,36 | 1,00 | crítica | 2,78 | 0,10 | 4,5 | 1,08 | 0,0 | 8,2 |

| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | Límite de colapso sintético alcanzado (gasto / déficit) |
|---|---|---|---|---|
| 1 | ↑ ↑ ↑ ↑ ↑ | 1 | 31,3 | no / 65 |
| 2,5 | = = ↑ ↑ ↑ | 37 | 4,5 | no / no |

**G · demanda alta con entrega conservada** — demanda × 1,5 todo el tiempo.

| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | Carga gasto | Carga déficit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 15 | 1,00 | 1,50 | crítica | 1,50 | 0,50 | 6,7 | 1,03 | 0,0 | 5,0 |
| 1 | 30 | 1,00 | 1,50 | crítica | 1,50 | 0,50 | 11,9 | 1,09 | 0,0 | 10,0 |
| 1 | 60 | 1,00 | 1,50 | crítica | 1,50 | 0,50 | 19,1 | 1,26 | 0,0 | 20,0 |
| 1 | 90 | 1,00 | 1,50 | crítica | 1,50 | 0,50 | 23,4 | 1,44 | 0,0 | 30,0 |
| 1 | 120 | 1,00 | 1,50 | crítica | 1,50 | 0,50 | 26,0 | 1,60 | 0,0 | 40,0 |
| 2,5 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 15 | 1,00 | 1,50 | compensada | 1,50 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 30 | 1,00 | 1,50 | compensada | 1,50 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 60 | 1,00 | 1,50 | compensada | 1,50 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 90 | 1,00 | 1,50 | compensada | 1,50 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 120 | 1,00 | 1,50 | compensada | 1,50 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |

| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | Límite de colapso sintético alcanzado (gasto / déficit) |
|---|---|---|---|---|
| 1 | ↑ ↑ ↑ ↑ ↑ | 1 | 26,0 | no / 91 |
| 2,5 | = = = = = | nunca | 0,0 | no / no |

**H · la reanimación restituye la entrega** — la bomba cae a 0,25 hasta el min 30 y se restituye a 1,0 hasta el min 60.

| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | Carga gasto | Carga déficit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 15 | 0,62 | 1,00 | crítica | 1,60 | 0,38 | 2,4 | 1,01 | 0,0 | 3,0 |
| 1 | 30 | 0,25 | 1,00 | crítica | 4,00 | 0,75 | 9,4 | 1,05 | 0,3 | 11,6 |
| 1 | 60 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 14,1 | 1,21 | 0,3 | 22,5 |
| 1 | 90 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 8,5 | 1,27 | 0,3 | 22,5 |
| 1 | 120 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 5,1 | 1,25 | 0,3 | 22,5 |
| 2,5 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 15 | 0,62 | 1,00 | compensada | 1,60 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 30 | 0,25 | 1,00 | crítica | 4,00 | 0,38 | 0,9 | 1,00 | 0,3 | 1,3 |
| 2,5 | 60 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 1,4 | 1,02 | 0,3 | 2,3 |
| 2,5 | 90 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,8 | 1,03 | 0,3 | 2,3 |
| 2,5 | 120 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,5 | 1,03 | 0,3 | 2,3 |

| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | Límite de colapso sintético alcanzado (gasto / déficit) |
|---|---|---|---|---|
| 1 | ↑ ↑ ↑ ↑ ↓ | 1 | 15,2 | no / no |
| 2,5 | = ↑ ↑ ↑ ↓ | 24 | 2,1 | no / no |

**I · la transfusión sube la Hb y la entrega** — la Hb baja a 4,6 g/dL hasta el min 30; +2 g/dL entre los min 45 y 85.

| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | Carga gasto | Carga déficit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 15 | 0,68 | 1,00 | crítica | 1,48 | 0,32 | 2,1 | 1,00 | 0,0 | 2,6 |
| 1 | 30 | 0,35 | 1,00 | crítica | 2,83 | 0,65 | 8,1 | 1,04 | 0,0 | 10,0 |
| 1 | 60 | 0,41 | 1,00 | crítica | 2,43 | 0,59 | 19,8 | 1,22 | 0,0 | 28,9 |
| 1 | 90 | 0,51 | 1,00 | crítica | 1,97 | 0,49 | 24,6 | 1,43 | 0,0 | 44,9 |
| 1 | 120 | 0,51 | 1,00 | crítica | 1,97 | 0,49 | 26,5 | 1,60 | 0,0 | 59,6 |
| 2,5 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 15 | 0,68 | 1,00 | compensada | 1,48 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 30 | 0,35 | 1,00 | crítica | 2,83 | 0,12 | 0,1 | 1,00 | 0,0 | 0,2 |
| 2,5 | 60 | 0,41 | 1,00 | compensada | 2,43 | 0,00 | 1,9 | 1,02 | 0,0 | 2,5 |
| 2,5 | 90 | 0,51 | 1,00 | compensada | 1,97 | 0,00 | 1,1 | 1,03 | 0,0 | 2,5 |
| 2,5 | 120 | 0,51 | 1,00 | compensada | 1,97 | 0,00 | 0,7 | 1,03 | 0,0 | 2,5 |

| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | Límite de colapso sintético alcanzado (gasto / déficit) |
|---|---|---|---|---|
| 1 | ↑ ↑ ↑ ↑ ↑ | 1 | 26,5 | no / 62 |
| 2,5 | = ↑ ↑ ↑ ↓ | 28 | 2,0 | no / no |

**J · déficit crítico grave y sostenido** — la bomba cae a 0,16 hasta el min 15 y se mantiene.

| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | Carga gasto | Carga déficit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 1 | 15 | 0,16 | 1,00 | crítica | 6,25 | 0,84 | 5,5 | 1,01 | 0,8 | 6,7 |
| 1 | 30 | 0,16 | 1,00 | crítica | 6,25 | 0,84 | 15,5 | 1,09 | 7,8 | 19,3 |
| 1 | 60 | 0,16 | 1,00 | crítica | 6,25 | 0,84 | 29,3 | 1,36 | 21,8 | 44,5 |
| 1 | 90 | 0,16 | 1,00 | crítica | 6,25 | 0,84 | 37,7 | 1,67 | 35,8 | 69,7 |
| 1 | 120 | 0,16 | 1,00 | crítica | 6,25 | 0,84 | 42,7 | 1,94 | 49,8 | 94,9 |
| 2,5 | 0 | 1,00 | 1,00 | adecuada | 1,00 | 0,00 | 0,0 | 1,00 | 0,0 | 0,0 |
| 2,5 | 15 | 0,16 | 1,00 | crítica | 6,25 | 0,60 | 1,0 | 1,00 | 0,8 | 1,6 |
| 2,5 | 30 | 0,16 | 1,00 | crítica | 6,25 | 0,60 | 8,8 | 1,04 | 7,8 | 10,6 |
| 2,5 | 60 | 0,16 | 1,00 | crítica | 6,25 | 0,60 | 19,6 | 1,22 | 21,8 | 28,6 |
| 2,5 | 90 | 0,16 | 1,00 | crítica | 6,25 | 0,60 | 26,1 | 1,44 | 35,8 | 46,6 |
| 2,5 | 120 | 0,16 | 1,00 | crítica | 6,25 | 0,60 | 30,0 | 1,64 | 49,8 | 64,6 |

| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | Límite de colapso sintético alcanzado (gasto / déficit) |
|---|---|---|---|---|
| 1 | ↑ ↑ ↑ ↑ ↑ | 1 | 42,7 | 78 / 43 |
| 2,5 | ↑ ↑ ↑ ↑ ↑ | 11 | 30,0 | 78 / 63 |

### 4.2 Hallazgo 1: entrega bajo la demanda pero recuperándose (L3)

Con la reserva canónica, 372 descensos sostenidos del lactato en una ventana L3 con sangrado activo y entrega bajo la demanda en cada minuto, con la entrega mejorando, en 207 candidatos (372 pares candidato–caso) de la región admisible; los pares se eligieron por esa mejora. Para cada variante: cuántos pares conservan un descenso sostenido dentro de un tramo **crítico** (déficit efectivo en cada minuto); cuántos están en recuperación en todos sus descensos (la entrega sube y el déficit efectivo baja entre los extremos y entre cada par de reevaluaciones de 15 min consecutivas); los estados de los minutos 0–30; y el cambio máximo de D o lactato frente a la corrida canónica.

| Reserva | Pares con descenso sostenido en tramo crítico | De ellos, en recuperación | Minutos 0–30 por estado | Cambio máx. de D o lactato |
|---|---|---|---|---|
| 1 (canónica) | 372 de 372 | 372 | crítica: 11532 | 0,000 |
| 2, banda fija | 0 de 372 | 0 | compensada: 11532 | 7,508 |
| 2, banda re-anclada | 372 de 372 | 372 | crítica: 11532 | 0,000 |
| 2,5, banda fija | 0 de 372 | 0 | compensada: 11532 | 7,508 |
| 2,5, banda re-anclada | 372 de 372 | 372 | crítica: 11532 | 0,000 |
| 3, banda fija | 0 de 372 | 0 | compensada: 11532 | 7,508 |
| 3, banda re-anclada | 372 de 372 | 372 | crítica: 11532 | 0,000 |

### 4.3 Hallazgo 2: entrega muy baja sin tratar (L1)

El sobreviviente de P2I-2R (los 72 comprometidos, sin refiltrar) con la menor entrega al final, en cada variante; y sobre todos los sobrevivientes, cuántos dejan el lactato sin tratar de los 60 min fuera de la envolvente docente de FD-LAC-02/03 (cuyo límite inferior es el lactato de llegada; se leen los números aprobados, no se ejecuta la regla) y cuántos terminan con el lactato bajo el de llegada (descriptivo).

| Caso | Variante | Relación de llegada | Min | Gasto rel. | Hb / Hb llegada | Entrega | Estado | Déficit | D | Lactato | PAS | V (mL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 1 (canónica) | 0,60 | 0 | 1,00 | 1,00 | 0,60 | crítica | 0,40 | 0,0 | 4,40 | 88 | 0 |
| gi_bleed_57m | 1 (canónica) | 0,60 | 60 | 0,63 | 0,92 | 0,35 | crítica | 0,65 | 14,7 | 4,86 | 72 | -150 |
| gi_bleed_57m | 1 (canónica) | 0,60 | 120 | 0,20 | 0,84 | 0,10 | crítica | 0,90 | 23,1 | 6,79 | 26 | -300 |
| gi_bleed_57m | 2, banda fija | 0,60 | 0 | 1,00 | 1,00 | 0,60 | compensada | 0,00 | 0,0 | 4,40 | 88 | 0 |
| gi_bleed_57m | 2, banda fija | 0,60 | 60 | 0,63 | 0,92 | 0,35 | crítica | 0,30 | 3,7 | 3,60 | 72 | -150 |
| gi_bleed_57m | 2, banda fija | 0,60 | 120 | 0,20 | 0,84 | 0,10 | crítica | 0,80 | 16,9 | 4,61 | 26 | -300 |
| gi_bleed_57m | 2, banda re-anclada | 0,30 | 0 | 1,00 | 1,00 | 0,30 | crítica | 0,40 | 0,0 | 4,40 | 88 | 0 |
| gi_bleed_57m | 2, banda re-anclada | 0,30 | 60 | 0,63 | 0,92 | 0,17 | crítica | 0,65 | 14,7 | 4,86 | 72 | -150 |
| gi_bleed_57m | 2, banda re-anclada | 0,30 | 120 | 0,20 | 0,84 | 0,05 | crítica | 0,90 | 23,1 | 6,79 | 26 | -300 |
| gi_bleed_57m | 2,5, banda fija | 0,60 | 0 | 1,00 | 1,00 | 0,60 | compensada | 0,00 | 0,0 | 4,40 | 88 | 0 |
| gi_bleed_57m | 2,5, banda fija | 0,60 | 60 | 0,63 | 0,92 | 0,35 | crítica | 0,13 | 0,6 | 3,46 | 72 | -150 |
| gi_bleed_57m | 2,5, banda fija | 0,60 | 120 | 0,20 | 0,84 | 0,10 | crítica | 0,75 | 14,0 | 3,98 | 26 | -300 |
| gi_bleed_57m | 2,5, banda re-anclada | 0,24 | 0 | 1,00 | 1,00 | 0,24 | crítica | 0,40 | 0,0 | 4,40 | 88 | 0 |
| gi_bleed_57m | 2,5, banda re-anclada | 0,24 | 60 | 0,63 | 0,92 | 0,14 | crítica | 0,65 | 14,7 | 4,86 | 72 | -150 |
| gi_bleed_57m | 2,5, banda re-anclada | 0,24 | 120 | 0,20 | 0,84 | 0,04 | crítica | 0,90 | 23,1 | 6,79 | 26 | -300 |
| gi_bleed_57m | 3, banda fija | 0,60 | 0 | 1,00 | 1,00 | 0,60 | compensada | 0,00 | 0,0 | 4,40 | 88 | 0 |
| gi_bleed_57m | 3, banda fija | 0,60 | 60 | 0,63 | 0,92 | 0,35 | compensada | 0,00 | 0,0 | 3,45 | 72 | -150 |
| gi_bleed_57m | 3, banda fija | 0,60 | 120 | 0,20 | 0,84 | 0,10 | crítica | 0,71 | 11,5 | 3,58 | 26 | -300 |
| gi_bleed_57m | 3, banda re-anclada | 0,20 | 0 | 1,00 | 1,00 | 0,20 | crítica | 0,40 | 0,0 | 4,40 | 88 | 0 |
| gi_bleed_57m | 3, banda re-anclada | 0,20 | 60 | 0,63 | 0,92 | 0,12 | crítica | 0,65 | 14,7 | 4,86 | 72 | -150 |
| gi_bleed_57m | 3, banda re-anclada | 0,20 | 120 | 0,20 | 0,84 | 0,03 | crítica | 0,90 | 23,1 | 6,79 | 26 | -300 |
| gi_bleed_72f | 1 (canónica) | 0,60 | 0 | 1,00 | 1,00 | 0,60 | crítica | 0,40 | 0,0 | 3,40 | 98 | 0 |
| gi_bleed_72f | 1 (canónica) | 0,60 | 60 | 0,76 | 0,92 | 0,42 | crítica | 0,58 | 13,5 | 4,19 | 87 | -150 |
| gi_bleed_72f | 1 (canónica) | 0,60 | 120 | 0,47 | 0,83 | 0,23 | crítica | 0,77 | 20,1 | 6,04 | 71 | -300 |
| gi_bleed_72f | 2, banda fija | 0,60 | 0 | 1,00 | 1,00 | 0,60 | compensada | 0,00 | 0,0 | 3,40 | 98 | 0 |
| gi_bleed_72f | 2, banda fija | 0,60 | 60 | 0,76 | 0,92 | 0,42 | crítica | 0,17 | 1,7 | 2,90 | 87 | -150 |
| gi_bleed_72f | 2, banda fija | 0,60 | 120 | 0,47 | 0,83 | 0,23 | crítica | 0,53 | 10,7 | 3,52 | 71 | -300 |
| gi_bleed_72f | 2, banda re-anclada | 0,30 | 0 | 1,00 | 1,00 | 0,30 | crítica | 0,40 | 0,0 | 3,40 | 98 | 0 |
| gi_bleed_72f | 2, banda re-anclada | 0,30 | 60 | 0,76 | 0,92 | 0,21 | crítica | 0,58 | 13,5 | 4,19 | 87 | -150 |
| gi_bleed_72f | 2, banda re-anclada | 0,30 | 120 | 0,47 | 0,83 | 0,12 | crítica | 0,77 | 20,1 | 6,04 | 71 | -300 |
| gi_bleed_72f | 2,5, banda fija | 0,60 | 0 | 1,00 | 1,00 | 0,60 | compensada | 0,00 | 0,0 | 3,40 | 98 | 0 |
| gi_bleed_72f | 2,5, banda fija | 0,60 | 60 | 0,76 | 0,92 | 0,42 | compensada | 0,00 | 0,0 | 2,85 | 87 | -150 |
| gi_bleed_72f | 2,5, banda fija | 0,60 | 120 | 0,47 | 0,83 | 0,23 | crítica | 0,41 | 6,7 | 2,91 | 71 | -300 |
| gi_bleed_72f | 2,5, banda re-anclada | 0,24 | 0 | 1,00 | 1,00 | 0,24 | crítica | 0,40 | 0,0 | 3,40 | 98 | 0 |
| gi_bleed_72f | 2,5, banda re-anclada | 0,24 | 60 | 0,76 | 0,92 | 0,17 | crítica | 0,58 | 13,5 | 4,19 | 87 | -150 |
| gi_bleed_72f | 2,5, banda re-anclada | 0,24 | 120 | 0,47 | 0,83 | 0,09 | crítica | 0,77 | 20,1 | 6,04 | 71 | -300 |
| gi_bleed_72f | 3, banda fija | 0,60 | 0 | 1,00 | 1,00 | 0,60 | compensada | 0,00 | 0,0 | 3,40 | 98 | 0 |
| gi_bleed_72f | 3, banda fija | 0,60 | 60 | 0,76 | 0,92 | 0,42 | compensada | 0,00 | 0,0 | 2,85 | 87 | -150 |
| gi_bleed_72f | 3, banda fija | 0,60 | 120 | 0,47 | 0,83 | 0,23 | crítica | 0,30 | 3,4 | 2,63 | 71 | -300 |
| gi_bleed_72f | 3, banda re-anclada | 0,20 | 0 | 1,00 | 1,00 | 0,20 | crítica | 0,40 | 0,0 | 3,40 | 98 | 0 |
| gi_bleed_72f | 3, banda re-anclada | 0,20 | 60 | 0,76 | 0,92 | 0,14 | crítica | 0,58 | 13,5 | 4,19 | 87 | -150 |
| gi_bleed_72f | 3, banda re-anclada | 0,20 | 120 | 0,47 | 0,83 | 0,08 | crítica | 0,77 | 20,1 | 6,04 | 71 | -300 |

| Caso | Variante | Entrega al final, rango de los sobrevivientes | Límite de colapso sintético (gasto / déficit), el más bajo | Sobrevivientes fuera de la envolvente de 60 min | Sobrevivientes con lactato final bajo el de llegada | Cambio máx. de D o lactato |
|---|---|---|---|---|---|---|
| gi_bleed_57m | 1 (canónica) | 0,10–0,16 | no / 57 | 0 de 72 | 3 de 72 | 0,000 |
| gi_bleed_57m | 2, banda fija | 0,10–0,16 | no / 109 | 57 de 72 | 63 de 72 | 17,733 |
| gi_bleed_57m | 2, banda re-anclada | 0,05–0,08 | no / 57 | 0 de 72 | 3 de 72 | 0,000 |
| gi_bleed_57m | 2,5, banda fija | 0,10–0,16 | no / no | 57 de 72 | 72 de 72 | 22,306 |
| gi_bleed_57m | 2,5, banda re-anclada | 0,04–0,07 | no / 57 | 0 de 72 | 3 de 72 | 0,000 |
| gi_bleed_57m | 3, banda fija | 0,10–0,16 | no / no | 57 de 72 | 72 de 72 | 25,937 |
| gi_bleed_57m | 3, banda re-anclada | 0,03–0,05 | no / 57 | 0 de 72 | 3 de 72 | 0,000 |
| gi_bleed_72f | 1 (canónica) | 0,23–0,39 | no / 61 | 0 de 72 | 0 de 72 | 0,000 |
| gi_bleed_72f | 2, banda fija | 0,23–0,39 | no / no | 21 de 72 | 54 de 72 | 20,174 |
| gi_bleed_72f | 2, banda re-anclada | 0,12–0,20 | no / 61 | 0 de 72 | 0 de 72 | 0,000 |
| gi_bleed_72f | 2,5, banda fija | 0,23–0,39 | no / no | 21 de 72 | 66 de 72 | 25,269 |
| gi_bleed_72f | 2,5, banda re-anclada | 0,09–0,16 | no / 61 | 0 de 72 | 0 de 72 | 0,000 |
| gi_bleed_72f | 3, banda fija | 0,23–0,39 | no / no | 21 de 72 | 66 de 72 | 29,286 |
| gi_bleed_72f | 3, banda re-anclada | 0,08–0,13 | no / 61 | 0 de 72 | 0 de 72 | 0,000 |

### 4.4 Hallazgo 3: índice de entrega tras la transfusión (L3)

| Caso | Máximo del índice por relación de llegada (mín–máx, n) | El más alto: llegada, minuto, índice = gasto rel. × Hb rel. × relación, V | El mismo pico, banda re-anclada (índice sobre DO2 normal, estado) |
|---|---|---|---|
| gi_bleed_57m | 0,60: 1,30 (n 18); 0,85: 1,84 (n 51); 1,00: 2,16 (n 3) | 1,00, min 60: 2,16 = 1,82 × 1,19 × 1,00; V 482 mL | ρ 2: 1,08 (adecuada); ρ 2,5: 0,86 (compensada); ρ 3: 0,72 (compensada) |
| gi_bleed_72f | 0,60: 1,11 (n 18); 0,85: 1,57 (n 51); 1,00: 1,84 (n 3) | 1,00, min 60: 1,84 = 1,54 × 1,20 × 1,00; V 482 mL | ρ 2: 0,92 (compensada); ρ 2,5: 0,74 (compensada); ρ 3: 0,61 (compensada) |

### 4.5 Cargas de colapso sintéticas sobre la región admisible

Todas las corridas producidas por el motor (L1 sin tratar, L2 salino parcial, L3 manejo definitivo) con la reserva canónica, que da el mismo déficit crítico que cualquier reserva con la banda re-anclada. La carga sintética acumula y no se repaga.

| Escenario y caso | Corridas | Detenidas antes de 120 min | Críticas al final | Alcanzan el límite por gasto (más temprano) | Alcanzan el límite por déficit (más temprano) |
|---|---|---|---|---|---|
| L1 gi_bleed_57m | 1054 | 0 | 1054 | 0 (—) | 1054 (min 57) |
| L1 gi_bleed_72f | 1054 | 0 | 1054 | 0 (—) | 1054 (min 61) |
| L2 gi_bleed_57m | 1054 | 0 | 1054 | 0 (—) | 1054 (min 65) |
| L2 gi_bleed_72f | 1054 | 0 | 1054 | 0 (—) | 1054 (min 62) |
| L3 gi_bleed_57m | 1054 | 0 | 0 | 0 (—) | 0 (—) |
| L3 gi_bleed_72f | 1054 | 0 | 0 | 0 (—) | 0 (—) |

<!-- /generado:oxigeno -->

## 5. Lectura de las sondas A–J (P2I-2P-6)

Con la reserva ilustrativa (2,5), frente a la canónica (1). Las magnitudes del lactato vienen de las cinéticas por
defecto (TBD); importa la dirección.

- **A · normal:** adecuada siempre, sin déficit, D 0 y lactato estable, con ambas reservas.
- **B · entrega baja compensada (−30 %):**
  - con reserva 2,5: compensada (extracción requerida 1,43), sin déficit, D 0 y lactato estable;
  - con reserva 1: crítica desde el minuto 1, D sube a 15 y el lactato sube. Es el defecto de §2.
- **C · entrega que cae y cruza la región crítica:**
  - con reserva 2,5: compensada hasta el minuto 75 (entrega < 0,4). D nace al cruzar, y el lactato sube recién al final,
    con retraso;
  - con reserva 1: crítica desde el minuto 1.
- **D · anemia con gasto conservado:**
  - con reserva 2,5: compensada hasta Hb ≈ 5,2 g/dL (minuto 112) y apenas crítica al final;
  - con reserva 1: deuda desde el inicio.
- **E · gasto bajo con Hb conservada (0,3):** con reserva 2,5 es crítica desde el minuto 52, con déficit 0,26; D y el
  lactato suben después.
- **F · gasto bajo y anemia (0,6 × 0,6):** con reserva 2,5 es crítica desde el minuto 37 con un déficit menor (0,10). La
  combinación es lo que la vuelve crítica.
- **G · demanda alta con entrega conservada (× 1,5):**
  - con reserva 2,5: compensada (extracción 1,5), sin deuda;
  - con reserva 1: deuda con entrega normal, lo que no es fisiológico.
- **H · la reanimación restituye la entrega:**
  - con reserva 2,5: crítica sólo entre los minutos 24 y 36, aproximadamente, con poca deuda;
  - con ambas reservas, D deja de acumularse al restituir y el lactato sigue un poco elevado antes de bajar. Es la
    elevación continua después de restituir que admite la regla de fisiología primero.
- **I · la transfusión sube la Hb y la entrega:**
  - con reserva 2,5, la transfusión saca al paciente de la región crítica y queda compensado con Hb ≈ 6,6 g/dL;
  - con reserva 1 sigue «en déficit» indefinidamente.
- **J · déficit crítico grave y sostenido:** crítico desde el minuto 11 (reserva 2,5). D y el lactato suben sin pausa, y
  la carga sintética por déficit alcanza su límite antes que la carga por gasto (§8).

## 6. Hallazgos de P2I-2R revisados (P2I-2P-7)

Se repiten las sondas originales:
- **hallazgo 1:** sobre toda la región admisible, en L3;
- **hallazgos 2 y 3:** sobre los 72 sobrevivientes comprometidos.

No se vuelve a filtrar: el hallazgo 1 lee sólo los tramos críticos de L3, y los sobrevivientes se leen del JSON
comprometido.

Las clasificaciones de los hallazgos 1 y 3 dependen de leer la banda GI re-anclada (§3). Es la lectura de su diseño y
la única coherente con L1, pero su adopción, junto con ρ, es una decisión docente pendiente.

1. **L3: entrega de ~60 % a ~86–96 % con el lactato bajando — REINTERPRETADO (condicionado a la banda re-anclada).**
   - Con la reserva canónica se reproduce exacto: 372 instancias en 207 candidatos (§4.2). Los pares se eligieron
     porque la entrega mejora.
   - Con la banda re-anclada, los minutos 0–30 siguen siendo **críticos**. En las 372 instancias, el déficit efectivo
     baja entre los extremos del descenso y entre cada par de reevaluaciones de 15 min consecutivas.
   - Es el estado RECOVERING-BUT-STILL-SUBTHRESHOLD de la decisión FD-LAC-06, en el que el lactato puede bajar.
   - Con la banda fija y ρ ≥ 2 el hallazgo «desaparece» porque todo se vuelve compensado. Pero el precio es la
     contradicción del hallazgo 2, así que esa resolución es aparente.
   - La corrección estructural no lo elimina: lo explica la semántica de trayectoria de FD-LAC-06.
2. **Entrega sin tratar de ~10–39 % — SIGUE PRESENTE.**
   - En unidades de entrega crítica, el más bajo llega a 0,10 (57m) y 0,23 (72f) a los 120 min. Re-anclado, sobre lo
     normal, es todavía menos: 0,03–0,05 (57m) y 0,08–0,12 (72f) con ρ 2–3.
   - La PAS llega a 26 mmHg (57m), con pulso y lactato 6,8. Causas en §7.
   - Con la banda fija y reserva, además, el lactato L1 de los 60 min sale de la envolvente docente de FD-LAC-02/03
     (bajo el de llegada): en 57 de 72 sobrevivientes en 57m y en 21 de 72 en 72f.
     - Al final queda bajo el de llegada en 63–72 de 72 (57m) y en 54–66 de 72 (72f), con sangrado activo.
     - FD-LAC-01 no lo detectaría si «inadecuada» se lee como CRITICAL (§9), porque la ventana pasa a compensada. Lo
       contradicen la envolvente y la fisiología.
   - Con la reserva canónica, 3 de 72 sobrevivientes en 57m ya terminan L1 con el lactato bajo el de llegada a los
     120 min. Ninguna regla vigente lo juzga: FD-LAC-01 llega hasta los 60 min.
   - La reserva sola no resuelve nada y, con la banda fija, empeora la coherencia.
3. **Índice tras la transfusión de ~1,1–2,2 — REINTERPRETADO (artefacto de normalización, condicionado a la banda
   re-anclada).**
   - El máximo crece con el nivel de `arrival_delivery_ratio`: 1,30 / 1,84 / 2,16 en 57m, y 1,11 / 1,57 / 1,84 en 72f,
     para 0,6 / 0,85 / 1,0.
   - Leído como fue diseñado, está en unidades de la entrega **crítica**: 2,16 es «2,16 veces lo mínimo».
     - Con la reserva canónica 1, lo mínimo y lo normal coinciden, y la cifra se lee como 2,16 veces lo normal. De ahí
       nació el hallazgo.
   - Re-anclado:
     - 57m: 1,08 (adecuada, apenas sobre lo normal) con ρ 2, 0,86 con ρ 2,5 y 0,72 con ρ 3 (compensada);
     - 72f: 0,61–0,92, compensada.
   - No hay un exceso patológico de DO2: 1,08 veces lo normal tras la reanimación es plausible. No se recorta el
     índice.
   - Queda una observación aparte, que pertenece a la calibración de volumen y presión (fuera de alcance): el gasto
     relativo a la llegada sube a 1,5–1,8 con +482 mL.

## 7. Causa de la entrega muy baja sin tratar (P2I-2P-4)

Sondas de sólo lectura sobre el sobreviviente más bajo (§4.3). La respuesta es **E, una combinación**, con pesos
distintos:

- **C, mapeo volumen → gasto → presión (causa principal de la profundidad):**
  - con 300 mL más de pérdida (2,5 mL/min), el gasto relativo cae de 1,0 a 0,20 y la PAS de 88 a 26 mmHg;
  - la Hb sólo baja a 0,84 de la de llegada. La caída de la entrega es casi toda de gasto;
  - es la pendiente de la curva de precarga en la posición de llegada: calibración de volumen y presión, fuera de este
    paquete.
- **D, colapso terminal apagado (por qué sigue «vivo»):**
  - con PAS 26 y una entrega del 3–10 % de lo normal, un paciente real estaría en paro o al borde de él;
  - el núcleo no tiene la regla activa en GI;
  - el lactato moderado (6,8 a los 120 min) refleja además las cinéticas del lactato, que siguen TBD.
- **A, normalización (sólo etiqueta):** cambia el número informado (unidades críticas frente a normales), no la
  trayectoria.
- **B, reserva ausente (no es causa):** la reserva no sube la entrega, sólo mueve dónde empieza la deuda. Con la banda
  re-anclada la trayectoria es idéntica, y con la banda fija baja D y el lactato en vez de explicarlos.

## 8. Entrega crítica e interfaz con el colapso (P2I-2P-5)

**Requisito estructural:** una incapacidad profunda y sostenida de cubrir la demanda de O2 no puede quedar indefinidamente
compatible con un paciente estable con pulso. Hoy queda compatible: la regla está apagada, y además lee sólo el gasto.

**Recomendación (sin umbrales finales; el colapso canónico GI sigue apagado):**
1. **La carga de colapso debe consumir el déficit crítico de O2:** la fracción déficit efectivo / demanda.
   - Es 0 mientras la extracción compensa y crece con la profundidad y la duración.
   - Deja de crecer al salir de la región crítica. Si además se repaga, y con qué τ, es TBD: es
     `collapse_repayment_tau_min`, que por defecto mantiene la carga. El cálculo sintético de este paquete no la repaga.
   - Cubre las cuatro vías de falla del suministro: gasto bajo, anemia, hipoxemia y demanda alta.
2. **El gasto no debe ser un requisito previo de la carga.** Sigue siendo un criterio propio de falta de pulso: un gasto
   que llega a 0 con pulso ya detiene la corrida.
   - Alcanzado el límite de la carga, el paciente pierde el pulso aunque el gasto se conserve. Si el ritmo terminal es
     AESP o asistolia es TBD.
   - Si el gasto fuera una puerta obligatoria, la anemia extrema nunca colapsaría. En una prueba sintética (Hb de 13 hasta
     3,0 g/dL, el límite inferior del canal), la carga por gasto queda en 0 y la carga por déficit crece (9,1 a los
     120 min).
3. **D no debe alimentar la carga.**
   - Es una deuda histórica y repagable. Haría colapsar a un paciente ya restituido, con D todavía alta (sonda H), y
     ataría el colapso a la ganancia y al aclaramiento de la deuda, que son TBD.
   - El lactato tampoco: es un observable.
4. **Estado mental:**
   - hoy el nivel de conciencia lee sólo la PAS y la SpO2 por bandas;
   - leer el déficit crítico (hipoperfusión cerebral) es una extensión posible y TBD; no se implementó.
5. **La carga por déficit exige una reserva > 1.**
   - Con reserva 1 es inespecífica: las sondas B, D, G e I alcanzan el límite sintético con estados que en un paciente
     están compensados.
   - Elegir la señal de colapso y fijar la reserva son decisiones que van juntas.

**Evidencia sintética (umbral de gasto 0,3, límite 30 minutos a severidad plena; ambos ilustrativos):**
- J alcanza el límite por déficit al minuto 63 y por gasto al 78. H no lo alcanza por ninguna vía.
- Sobre toda la región admisible (§4.5), con la reserva canónica o la banda re-anclada:
  - las 1054 corridas L1 y las 1054 corridas L2 de cada caso siguen CRÍTICAS a los 120 min y alcanzan el límite por
    déficit (las más tempranas: L1 a los 57 min en 57m y 61 min en 72f; L2 a los 65 y 62 min). Ninguna lo alcanza por
    gasto;
  - ninguna corrida L3 lo alcanza ni termina crítica: con este límite, ningún paciente con manejo definitivo colapsaría.
- Con este límite ilustrativo, todo paciente sin tratar o sólo con salino colapsaría en 1–2 h. El límite real, su
  dependencia de la dinámica y el repago son decisiones docentes. Lo estructural es la separación: L1 y L2 críticos y
  sostenidos, frente a L3 restituido.

## 9. Cómo deberían leer FD-LAC-01 y FD-LAC-06 el estado corregido (P2I-2P-8)

Propuesta para la docencia. No se aplicó ni se volvió a filtrar.

- **«Entrega inadecuada»:** la definición confirmada es «inadequate delivery = oxygen delivery < oxygen demand». Debería
  leerse como **estado CRITICAL** (déficit efectivo > 0), no como «bajo lo normal».
  - Con ρ > 1, una entrega bajo lo normal pero sobre la crítica está compensada y no genera deuda: ni FD-LAC-01 ni
    FD-LAC-06 deberían aplicarse ahí.
  - Con la reserva canónica 1 y la banda como está, CRITICAL coincide exactamente con «entrega < demanda»: esta lectura,
    sola, no cambia ningún resultado (invariancia de §3).
- **FD-LAC-06, por intervalo de reevaluación** (15 min) dentro de una ventana CRITICAL con sangrado activo:
  - *persistente o en empeoramiento*: el estado sigue CRITICAL todo el intervalo y el déficit efectivo al final no es
    menor que al inicio (sin tendencia de recuperación, o empeorando). Un descenso sostenido del lactato aquí sigue
    rechazado;
  - *en recuperación todavía bajo el umbral*: el estado sigue CRITICAL, pero el déficit efectivo baja a lo largo del
    intervalo (la relación de suministro sube) durante una reanimación eficaz. El lactato puede bajar;
  - la transición de CRITICAL a COMPENSATED o ADEQUATE cierra la ventana;
  - sin tolerancia porcentual: dirección del déficit efectivo y transiciones de estado, como pidió la docencia;
  - queda para la docencia:
    - si la dirección se mide entre los extremos del intervalo o exige monotonía dentro de él;
    - si «reanimación eficaz» exige una orden activa.
- **FD-LAC-01 (L1 sin tratar):**
  - con la banda re-anclada, la ventana es CRITICAL con sangrado activo, nada cambia y lo prohibido sigue igual;
  - con la banda fija y ρ > 1, la ventana pasa a compensada y FD-LAC-01, leída como CRITICAL, deja de aplicarse. El
    lactato de los 60 min sale entonces de la envolvente de FD-LAC-02/03 (§6, hallazgo 2). Es la prueba de que reserva y
    banda se deciden juntas.
- **La definición congelada:** `faculty_constraints.adequate` compara hoy la entrega con la demanda sin la reserva. Al
  autorizar el refiltrado, debe pasar a «sin déficit crítico» (ρ × entrega ≥ demanda), con una nueva congelación de las
  definiciones.
- **FD-LAC-04/05 («entrega adecuada sostenida», T\*):**
  - se recomienda «sin déficit crítico» (COMPENSATED o ADEQUATE), que es donde la deuda deja de acumularse;
  - exigir ADEQUATE (sobre lo normal) dejaría NOT_EVALUABLE a pacientes transfundidos con metas restrictivas de Hb, que
    quedan compensados (sonda I);
  - lo decide la docencia.
- **D y lactato:** D integra sólo el déficit efectivo, y el lactato sigue leyendo D, no el estado de oxigenación
  directamente. Así se conservan el retraso, la disociación transitoria y la elevación después de restituir.

## 10. Parámetros que siguen TBD (ninguno aprobado)

- **Reserva y curva:** la reserva de extracción ρ (ilustrativa 2–3) y, con ella, la entrega crítica; la forma de la
  curva cerca del punto crítico.
- **Demanda:** la relectura de la banda de `arrival_delivery_ratio` junto con ρ; los multiplicadores de demanda;
  `metabolic_demand_baseline`.
- **Deuda y lactato:**
  - la ganancia déficit → D (`debt_per_delivery_deficit`) y τ_D;
  - la ganancia D → lactato (`lactate_per_output_deficit`) y τ_L.
- **Colapso:** la señal, el umbral, el límite, la carga por minuto, el repago y el ritmo terminal.
- **Otras decisiones:** la lectura del estado mental, y la operacionalización de FD-LAC-06 (dirección y monotonía) y de
  «adecuada» en FD-LAC-04/05.

## 11. Cambios, golden y artefactos

- **Núcleo:**
  - `derived.py`: el parámetro, `effective_oxygen_deficit`, `oxygen_balance` y los estados;
  - `integration.py`: D integra el déficit efectivo; el texto de procedencia de la deuda lo nombra;
  - `state.py`: definiciones de las anclas, sólo documentación;
  - `shadow.py`: la bandera del recorte «sin crédito» usa ρ × entrega;
  - `lactate_slice.py`: la guarda de la lectura de la banda.
- **Golden GI directo:** el diff completo son las 4 líneas de la entrada de metadatos `oxygen_extraction_reserve` en el
  mapa `PARAMETERS`. Ninguna cifra de escenario cambia, y la ruta Contracts v2 sigue IDÉNTICA.
- **Sondas:**
  - `clinical_core/oxygen_probes.py`, sólo lectura; están excluidas del digest del paquete P2G porque el paquete no las
    lee;
  - JSON en `docs/revision/P2I2P_oxygen_probes.json`;
  - su digest cubre todas las fuentes del núcleo.
- **Digests:**
  - el paquete P2G y el corte P2I-1 cambian de digest, porque cambiaron las fuentes del núcleo; se regeneraron con cifras
    idénticas;
  - el congelamiento de calibración no cambia;
  - P2I-2R queda PENDIENTE DE REFILTRADO (`RESULTS_PENDING_REFILTER`), y su comando rehúsa producir resultados nuevos.

## 12. Limitaciones

- Las reservas 2, 2,5 y 3 son ilustraciones, no propuestas. La orientación aritmética de §3 supone una Hb habitual que el
  caso no declara.
- Las sondas A–J usan la llegada neutra sana del arnés de bandas y cinéticas por defecto; no son pacientes GI.
- La carga de colapso se calculó fuera del núcleo, sobre cada trayectoria. La regla del núcleo no se cambió ni se activó.
- El hallazgo 1 se repitió con las definiciones de P2I-2R sobre tramos CRITICAL, sin filtro FD-LAC. Los hallazgos 2 y 3
  leen los sobrevivientes comprometidos con el núcleo anterior; como las cifras canónicas no cambian, son los mismos.
- La pendiente del gasto frente al volumen (hallazgos 2 y 3) es una observación para la calibración de volumen y presión,
  que este paquete no hace.
