# P2I-2AA · Cierre del borde de τ del cristaloide y semántica de la preparación del lactato

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni migra GI u otra familia;
- no ejecuta el filtro del lactato;
- no calibra la presión ni la FC, ni activa el colapso;
- no elige parámetros ocultos ni se ajusta al motor heredado;
- no cambia ninguna restricción docente: FD-BLD-04, 05 y 06 son las de P2I-2V-R, y el criterio robusto es el de
  P2I-2Z.

Código: `clinical_core/blood_fluid_tau_closure.py` (diseño, semántica, criterios y evaluación; congelado en `83996c5`
antes de evaluar y recongelado en `0b90ddf` por un hallazgo de la revisión, §9) y `clinical_core/blood_fluid_tau_closure_report.py` (sólo este informe). Números:
`docs/revision/P2I2AA_blood_fluid_tau_closure.json`. Registro de partida, cerrado: P2I-2Z (`e89a248e…`), cuyo veredicto
NOT_READY quedó aceptado.

## 1. Borde de τ (P2I-2AA-1 a 3)

<!-- generado:tau -->
Congelamiento de P2I-2AA: `5087cf022f928fed5d3893a00a4907578e7f91b3543ee10c6ba3786abde01001`, comprometido antes de evaluar (una prueba lo fija). Registros de partida: P2I-2Z `e89a248ef406acda8c17d95931da98eac9e92d8ab2c1c1fb5bd2e9bf0f20ecf4`, P2I-2Y `67e5b80a5a96f526fc2f9e5b2c721026f3ac71ba612fe9cb3e06f23106f4a8d4`.

Diseño: F0 0,2; Finf 0,05 y 0,1; τ 120, 150, 180, 210 y 240 min (10 puntos; τ 120 reproduce P2I-2Z; nada por encima de 240). Criterio robusto de P2I-2Z: FD-BLD-06 en las 48 claves de sangre, en los dos casos.

| Punto | FD-BLD-04 | FD-BLD-05 | FD-BLD-06 referencia | FD-BLD-06 todas las sondas | FD-BLD-06 todas las claves certificadas | Robusto | Aporte inicial | Retenido 30′ / 60′ / 120′ |
|---|---|---|---|---|---|---|---|---|
| F0 0,2 · Finf 0,05 · τ 120 | pasa | pasa | pasa | pasa | pasa | **sí** | 0,188 | 0,177 / 0,149 / 0,110 |
| F0 0,2 · Finf 0,05 · τ 150 | pasa | pasa | pasa | pasa | pasa | **sí** | 0,190 | 0,181 / 0,157 / 0,122 |
| F0 0,2 · Finf 0,05 · τ 180 | pasa | pasa | pasa | pasa | pasa | **sí** | 0,192 | 0,184 / 0,163 / 0,131 |
| F0 0,2 · Finf 0,05 · τ 210 | pasa | pasa | pasa | pasa | pasa | **sí** | 0,193 | 0,186 / 0,168 / 0,139 |
| F0 0,2 · Finf 0,05 · τ 240 | pasa | pasa | pasa | pasa | pasa | **sí** | 0,194 | 0,188 / 0,172 / 0,145 |
| F0 0,2 · Finf 0,1 · τ 120 | pasa | pasa | pasa | pasa | pasa | **sí** | 0,192 | 0,184 / 0,166 / 0,140 |
| F0 0,2 · Finf 0,1 · τ 150 | pasa | pasa | pasa | pasa | pasa | **sí** | 0,193 | 0,187 / 0,171 / 0,148 |
| F0 0,2 · Finf 0,1 · τ 180 | pasa | falla | pasa | pasa | pasa | **no** | 0,194 | 0,189 / 0,176 / 0,154 |
| F0 0,2 · Finf 0,1 · τ 210 | pasa | falla | pasa | pasa | pasa | **no** | 0,195 | 0,191 / 0,179 / 0,159 |
| F0 0,2 · Finf 0,1 · τ 240 | pasa | falla | pasa | pasa | pasa | **no** | 0,196 | 0,192 / 0,181 / 0,163 |

| Finf | τ con sobreviviente robusto | Mayor τ que sobrevive | Primer τ sin sobreviviente |
|---|---|---|---|
| 0,05 | 120, 150, 180, 210, 240 | 240 | ninguno |
| 0,1 | 120, 150 | 150 | 180 |

Mayor τ con sobreviviente: **240**. Primer τ probado sin sobreviviente: **ninguno**. Clasificación: **TAU_REMAINS_OPEN_AT_240**. La extensión se detiene: nada por encima de 240 sin decisión docente.
<!-- /generado:tau -->

### 1.1 Lectura

- **τ 120 reproduce P2I-2Z.** Coinciden los veredictos de FD-BLD-04 y 05, y los de FD-BLD-06 en las 48 claves; la
  corrida lo comprueba antes de seguir.
- **FD-BLD-04 y FD-BLD-06 pasan en los 10 puntos**, en las 48 claves y en los dos casos. Lo que separa es FD-BLD-05 a
  los 120 min (techo 0,15):
  - **Finf 0,1:** τ 150 deja 0,148 y pasa; τ 180 deja 0,154 y falla, igual que 210 (0,159) y 240 (0,163). Para este
    Finf el borde queda **cerrado dentro del dominio probado**: el último τ que sobrevive es 150 y el primero que
    falla, 180.
  - **Finf 0,05:** 0,110, 0,122, 0,131, 0,139 y 0,145 con τ 120, 150, 180, 210 y 240. Todos pasan. Con τ 240 el
    margen es de 0,005.
- **Clasificación de conjunto: TAU_REMAINS_OPEN_AT_240.** El mayor τ con sobreviviente robusto es 240 (con Finf
  0,05), y no hay ningún τ probado sin sobreviviente. Según la regla congelada, la extensión se detiene y no se agrega
  nada por encima de 240.
- **Lo que se observa sin extrapolar:** con Finf 0,05, cada paso de 30 min acerca la lectura al techo cada vez menos
  (+0,012, +0,009, +0,007, +0,006), y el margen que queda en 240 (0,005) es menor que el último paso. No dice en qué τ
  fallaría.

## 2. Soporte candidato del cristaloide

<!-- generado:region -->
Soporte candidato (puntos activos, Finf < F0): F0 0,2 · Finf 0,05 · τ 60, F0 0,2 · Finf 0,05 · τ 90, F0 0,2 · Finf 0,05 · τ 120, F0 0,2 · Finf 0,05 · τ 150, F0 0,2 · Finf 0,05 · τ 180, F0 0,2 · Finf 0,05 · τ 210, F0 0,2 · Finf 0,05 · τ 240, F0 0,2 · Finf 0,1 · τ 30, F0 0,2 · Finf 0,1 · τ 60, F0 0,2 · Finf 0,1 · τ 90, F0 0,2 · Finf 0,1 · τ 120, F0 0,2 · Finf 0,1 · τ 150.

| Parámetro | Explorado | Soporte candidato | Clase | Lado inferior | Lado superior | Borde | Identificado (regla congelada) |
|---|---|---|---|---|---|---|---|
| F0 | 0,15, 0,2, 0,25, 0,3, 0,35 | 0,2 | WELL_CONSTRAINED | acotado por restricción | acotado por restricción | INTERIOR | sí |
| Finf | 0, 0,05, 0,1, 0,15, 0,2 | 0,05, 0,1 | PARTIALLY_CONSTRAINED | acotado por restricción | acotado por restricción | INTERIOR | no |
| tau | 15, 30, 60, 90, 120, 150, 180, 210, 240 | 30, 60, 90, 120, 150, 180, 210, 240 | PARTIALLY_CONSTRAINED | acotado por restricción | abierto (borde de la grilla) | OPEN_UPPER_GRID_EDGE | no |
<!-- /generado:region -->

### 2.1 Lectura

- **Soporte: 12 puntos activos (Finf < F0), todos con F0 0,2.**
  - Con Finf 0,05: τ 60 a 240.
  - Con Finf 0,1: τ 30 a 150.
  - Los puntos por debajo de 120 vienen de P2I-2Z y no se reevaluaron.
- **F0 0,2:** la regla congelada lo marca «identificado», con la misma salvedad que en P2I-2Z. Sus vecinos se
  exploraron sólo con τ ≤ 60; con τ ≥ 90 la docencia lo fijó.
- **Finf 0,05–0,1:** PARTIALLY_CONSTRAINED e INTERIOR. Sus vecinos también se exploraron sólo con τ ≤ 60.
- **τ 30–240:** el lado inferior lo acota una restricción y el superior queda abierto en el borde de la grilla. No está
  identificado: que Finf 0,1 falle con τ 180 no identifica τ.
- **Sin aprobaciones:** no hay «mejor combinación» y nada es FACULTY_APPROVED.

## 3. Identificabilidad práctica de τ en el horizonte de 120 min (P2I-2AA-4)

<!-- generado:practico -->
Identificabilidad estructural: STRUCTURALLY_IDENTIFIABLE (Finf < F0); STRUCTURALLY_NON_IDENTIFIABLE cuando Finf == F0. Clasificación práctica (horizonte de 120 min, frente a las restricciones docentes): **CONSTRAINT_BOUNDED_BEYOND_TESTED_DOMAIN**.

| Margen con τ 240 (distancia al borde más cercano) | Finf 0,05 | Finf 0,1 | Límite τ → ∞ (Finf = F0, sólo referencia) |
|---|---|---|---|
| FD-BLD-04 (aporte inicial) | 0,044 | 0,046 | 0,050 |
| FD-BLD-05 a los 30′ | 0,038 | 0,042 | 0,050 |
| FD-BLD-05 a los 60′ | 0,028 | 0,019 | 0,000 |
| FD-BLD-05 a los 120′ | 0,005 | -0,013 | -0,050 |
| FD-BLD-06 pico con 1 L | 0,031 | 0,034 | 0,039 |
| FD-BLD-06 pico con 2 L | 0,026 | 0,018 | 0,003 |
| FD-BLD-06 reversión parcial con 1 L | 0,069 | 0,049 | 0,010 |
| FD-BLD-06 reversión parcial con 2 L | 0,144 | 0,107 | 0,037 |

| Finf | Monótono en τ | Mayor cambio 210 → 240 (retenido) | Mayor cambio 210 → 240 (cualquier lectura) | Distancia de 240 al límite (retenido) | Distancia de 240 al límite (cualquier lectura) |
|---|---|---|---|---|---|
| 0,05 | sí | 0,006 | 0,023 | 0,055 | 0,204 |
| 0,1 | sí | 0,004 | 0,015 | 0,037 | 0,137 |

Límite τ → ∞ (F0 0,2 · Finf 0,2 · τ 240, REFERENCE_ONLY): FD-BLD-04 pasa, FD-BLD-05 falla, FD-BLD-06 pasa (48 claves, dos casos).

Diferencias en el horizonte (representativo medio de sangre, 1 L y 2 L, minutos 0–120, los dos casos):

| Finf | Comparación | retenido | dilución de Hb (g/dL) | gasto relativo | DO2 | déficit crítico |
|---|---|---|---|---|---|---|
| 0,05 | τ 210 frente a 240 | 0,006 | 0,016 | 0,008 | 0,002 | 0,005 |
| 0,05 | τ 240 frente al límite | 0,055 | 0,145 | 0,074 | 0,017 | 0,041 |
| 0,1 | τ 210 frente a 240 | 0,004 | 0,011 | 0,006 | 0,001 | 0,003 |
| 0,1 | τ 240 frente al límite | 0,037 | 0,095 | 0,049 | 0,011 | 0,027 |
<!-- /generado:practico -->

### 3.1 Lectura

- **Estructural.** Con Finf < F0, τ fija la velocidad con que sale el transitorio y llega a cada lectura de lo retenido:
  es STRUCTURALLY_IDENTIFIABLE. Con Finf = F0 no actúa.
- **Práctica, frente a las restricciones: CONSTRAINT_BOUNDED_BEYOND_TESTED_DOMAIN.**
  - **Monotonía:** todas las lecturas son monótonas en τ en los valores probados.
  - **El límite falla:** cuando τ → ∞ no sale nada, y el estado es el de Finf = F0 (sólo referencia). Ese límite
    retiene 0,20 a los 30, 60 y 120 min y **falla FD-BLD-05 a los 120 min** (techo 0,15).
  - **Consecuencia:** entre 240 y el límite hay un τ finito donde FD-BLD-05 empieza a fallar. Una restricción docente
    depende entonces de una cota que está más allá del dominio probado.
- **Práctica, dentro del horizonte de 120 min:**
  - **Entre τ 210 y 240 las diferencias son pequeñas.** Con Finf 0,05, en el representativo medio de sangre: retenido
    0,006, dilución de Hb 0,016 g/dL, gasto 0,008, DO2 0,002 y déficit 0,005.
  - **Hasta el límite, no lo son:** retenido 0,055, dilución 0,145 g/dL, gasto 0,074, DO2 0,017 y déficit 0,041.
- **Confusión práctica entre Finf y τ.** Dentro del horizonte, un Finf mayor con un τ menor se parece a un Finf menor
  con un τ mayor:
  - Finf 0,05 · τ 240 retiene 0,188 / 0,172 / 0,145 (30′ / 60′ / 120′); Finf 0,1 · τ 150 retiene 0,187 / 0,171 /
    0,148;
  - Finf 0,05 · τ 210 retiene 0,186 / 0,168 / 0,139; Finf 0,1 · τ 120, 0,184 / 0,166 / 0,140.

  En 120 min, τ no es identificable en la práctica por separado de Finf. Lo que las restricciones acotan es la curva de
  lo retenido, no cada parámetro.
- **Nota de lectura de la tabla:** la columna «cualquier lectura» mezcla unidades (fracciones de lo retenido y
  diluciones en g/dL). Su 0,204 es una dilución.

## 4. Decisiones docentes registradas

<!-- generado:semantica -->
| Decisión docente (2026-10-28) | Registro | Comprobación |
|---|---|---|
| Adecuación del oxígeno para el lactato | déficit efectivo = 0 (ADEQUATE y COMPENSATED); CRITICAL si > 0 | 84 combinaciones de entrega, demanda y reserva: coinciden con los estados del núcleo |
| Tasas del futuro espacio del lactato | 2,5, 5, 6 | sin preeliminar ninguna |
| gi_fraction_after_hemostasis (FD-25) | 0,1: FIXED_PROVISIONAL_FOR_PRIMARY_LACTATE_ANALYSIS + FACULTY_DECISION_PENDING | rango comprometido: no (registro 0,1–0,1); sensibilidad: ninguna (no se inventa un rango) |
| gi_fraction_with_ppi (FD-24) | 0,8: FIXED_PROVISIONAL_FOR_PRIMARY_LACTATE_ANALYSIS + FACULTY_DECISION_PENDING | rango comprometido: no (registro 0,8–0,8); sensibilidad: ninguna (no se inventa un rango) |
<!-- /generado:semantica -->

### 4.1 Lectura

- **Adecuación del oxígeno para el lactato (fijada, no aplicada):**
  - adecuada si el déficit efectivo es 0, sea ADEQUATE o COMPENSATED; CRITICAL si es > 0;
  - no exige volver a la entrega normal antes de que el lactato pueda aclararse;
  - coincide con los estados del núcleo en las 84 combinaciones de la grilla;
  - con la banda re-anclada, ni el déficit ni la etiqueta cambian con ρ (§5);
  - `faculty_constraints.adequate` sigue congelada (lee entrega ≥ demanda con tolerancia, es decir, la entrega normal):
    el paquete del lactato debe aplicar esta regla.
- **Tasas:** el futuro espacio del lactato incluye 2,5, 5 y 6.
  - La 2,5 sobrevivió en P2I-2V-R (2628 conjuntos) y en las cajas de extensión de P2I-2W dentro de la banda (meta 1,0:
    264; meta 1,0 con τ 480: 756), siempre en la posición superior de la banda. Son 3648 conjuntos, y ninguna
    restricción vigente la excluye.
  - P2I-2W extendió el relleno sobre las tasas 2,5 y 5. La primera versión congelada de este paquete omitía esas
    cajas para la 2,5 y el informe decía, en falso, que la extensión sólo se había probado con 5 a 7. La revisión lo
    detectó y se recongeló (§9).
- **Modificadores de L3:** el registro no tiene un rango comprometido, porque el inferior, el medio y el superior son
  el mismo valor.
  - Quedan FIXED_PROVISIONAL_FOR_PRIMARY_LACTATE_ANALYSIS y FACULTY_DECISION_PENDING (FD-24 y FD-25, abiertas en P2G).
  - No se inventa un rango ni se prepara una sensibilidad.
  - No bloquean la preparación: sin el lactato no hay evidencia de sensibilidad.

## 5. Claves de sangre y comprobaciones estructurales

<!-- generado:claves -->
Tasa 2,5: FD-BLD-06 de los 12 puntos del soporte en las 63 claves de la tasa 2,5 (superconjunto de las de sus sobrevivientes, de P2I-2V-R y de P2I-2W), en los dos casos: todos pasan.

Completitud de la sustitución: 387 claves exploradas de las tasas 2,5, 5 y 6; cristaloides viejos que cumplen FD-BLD-04 y 05: 9 de la grilla de P2I-2V-R y 9 de los valores de P2I-2Y. Claves sin testigo (excluidas sólo por el cristaloide viejo): **0**.

| Comprobación estructural | Resultado |
|---|---|
| ρ no mueve el déficit efectivo ni la etiqueta de adecuación | sí |
| el nivel de entrega de llegada no mueve la hemodinámica | sí |
| el nivel de entrega de llegada sí mueve el déficit | sí |
| (P2I-2Z, repetidas) cinética del lactato y de la deuda sin efecto en la hemodinámica; ρ se cancela en D y el lactato | sí |
<!-- /generado:claves -->

### 5.1 Lectura

- **Tasa 2,5:** los 12 puntos del soporte pasan FD-BLD-06 en las 63 claves de la tasa 2,5, en los dos casos: 36 de
  P2I-2V-R y 27 de las cajas de P2I-2W. No hay pares a excluir.
- **Completitud de la sustitución:** en las 387 claves exploradas de las tasas 2,5, 5 y 6, que incluyen las de todas
  las cajas de P2I-2W dentro de la banda, algún cristaloide viejo que cumple FD-BLD-04 y 05 pasa FD-BLD-06 en los dos
  casos.
  - Así, ninguna clave quedó fuera sólo por el cristaloide viejo: FD-BLD-06 no lee la posición, y ninguna otra
    restricción lee la bolsa.
  - Reemplazar el cristaloide por el soporte nuevo no pierde candidatos de sangre.
- **Comprobaciones estructurales (nuevas):**
  - ρ no mueve el déficit efectivo ni la etiqueta de adecuación;
  - el nivel de entrega de llegada no mueve la hemodinámica, aunque sí el déficit.

  Junto con las de P2I-2Z, que siguen valiendo, sostienen el diseño factorizado de §7.

## 6. Preparación para reconstruir el lactato (P2I-2AA-5)

<!-- generado:preparacion -->
| Criterio | Resultado |
|---|---|
| BloodState compartido activo | cumple |
| modelo de DO2 y extracción vigente | cumple |
| región de precarga compatible con el caso definida | cumple |
| soporte de la tasa de sangrado caracterizado (2,5, 5 y 6) | cumple |
| soporte candidato del cristaloide caracterizado | **no cumple** |
| ninguna sonda de hemorragia activa y obsoleta evita el BloodState | cumple |
| parámetros ocultos sin aprobar y soporte candidato explícito | cumple |
| semántica de la adecuación del oxígeno fijada | cumple |

**Veredicto: NOT_READY** — soporte candidato del cristaloide caracterizado.
<!-- /generado:preparacion -->

### 6.1 Lectura

**NOT_READY — soporte candidato del cristaloide caracterizado.** Los otros siete criterios se cumplen, incluida la
semántica de la adecuación.

**Qué dice la regla congelada.** No mide diferencias en el horizonte: sólo mira si el límite τ → ∞ cumple las
restricciones.
- Si las cumple: CONSTRAINT_INDISTINGUISHABLE_BEYOND_240, el rango se propaga y el criterio pasa.
- Si falla alguna: CONSTRAINT_BOUNDED_BEYOND_TESTED_DOMAIN y el criterio no pasa.

El límite falla FD-BLD-05 a los 120 min (margen −0,05), así que el veredicto es NOT_READY. No se fuerza un cierre
numérico para obtener READY.

**Las tres condiciones de la docencia, leídas aparte** (es una lectura, no la regla):
1. **Incertidumbre prácticamente no identificable en el horizonte: pequeña.** Cualquier τ > 240 que sobreviva debe
   dejar lo retenido a los 120 min entre 0,145 (τ 240) y el techo de 0,15. Lo que queda por resolver en esa lectura es
   ≤ 0,005. Entre τ 210 y 240 el resto del horizonte también cambia poco (§3). La distancia al límite (0,055) no mide
   esa incertidumbre, porque el límite está excluido por la propia FD-BLD-05.
2. **El rango que sobrevive se puede propagar: en lo probado, sí.** Con Finf 0,05 es τ 60–240 y con Finf 0,1, τ
   30–150. La regla sólo certifica la propagación de τ > 240 cuando el límite cumple las restricciones, y aquí no las
   cumple.
3. **Ninguna restricción depende de una cota más precisa: no se cumple.** FD-BLD-05 a los 120 min acota τ con
   Finf 0,05 en algún valor finito más allá de 240.

**Qué lo destraba (decisión docente):**
- aceptar τ ≤ 240 como soporte con Finf 0,05, con la cota de FD-BLD-05 declarada más allá de 240; el margen que queda
  es de 0,005;
- o autorizar un valor más de τ, congelado antes de evaluar;
- o tratar Finf y τ como una sola curva de lo retenido para el lactato, dado que dentro del horizonte se confunden (§3).
  Con τ ≥ 90 no se probó ningún vecino de Finf (0 ni 0,15): esta opción tendría que decir qué hacer con ellos.

## 7. Espacio de origen del próximo paquete del lactato (P2I-2AA-6 y 7)

<!-- generado:espacio -->
Estado: **DRAFT — NOT EXECUTABLE UNTIL BLOOD/FLUID READINESS = READY (borrador: no se ejecuta)**.

| Tasa | Fuente | Sobrevivientes conjuntos | P1 (L1, L2) | P3 (L3) |
|---|---|---|---|---|
| 2,5 | sobrevivientes conjuntos de P2I-2V-R y de las cajas de extensión de P2I-2W dentro de la banda (meta del relleno 1,0; 1,0 con τ 480) | 3648 | 16–189 | 136–1701 |
| 5 | sobrevivientes conjuntos de P2I-2Y (con la extensión del relleno) | 3423 | 27–81 | 135–729 |
| 6 | sobrevivientes conjuntos de P2I-2Y (con la extensión del relleno) | 2268 | 18–54 | 90–486 |

Posición: 57m 0,5; 72f 0,6. Cristaloide: 12 puntos. ρ: banda 2,0–3,0, simulada con 2,5 (lactato y adecuación invariantes: sí).

| Recuento (antes de simular) | Mínimo | Máximo |
|---|---|---|
| Candidatos (conjuntos) | 1754460 | 14171760 |
| Trayectorias hemodinámicas únicas (simulaciones del núcleo, diseño factorizado) | 2308 | 14256 |
| Posprocesos por trayectoria hemodinámica (sin simular) | 405 | 405 |
| Simulaciones del producto ingenuo | 94740840 | 765275040 |
| Simulaciones evitadas | 94738532 | 765260784 |

Factorización válida según las comprobaciones estructurales: **sí**.
<!-- /generado:espacio -->

### 7.1 Lectura del borrador

**DRAFT — NOT EXECUTABLE UNTIL BLOOD/FLUID READINESS = READY.** El espacio no puede usarse como entrada certificada
mientras el veredicto sea NOT_READY: `certified_input` lo rechaza, y una prueba lo fija. Se construye desde la
fisiología actual y no usa la región histórica de P2F de 1054 conjuntos.

- **A. Sangre:**
  - **Tasas 5 y 6:** los sobrevivientes conjuntos de P2I-2Y.
  - **Tasa 2,5:** los de P2I-2V-R (2628) y los de las cajas de extensión de P2I-2W dentro de la banda (1020): 3648.
  - **Proyecciones:** P1 (tasa, B0, λ/κ y relleno; basta para L1 y L2) entre 61 y 324 conjuntos; P3 (P1 × la unidad
    de glóbulos rojos; para L3) entre 361 y 2916.
  - **Enumeración exacta:** una sola vez, en el próximo paquete, con las lógicas congeladas.
- **B. Posición:** 57m 0,5 y 72f 0,6, las únicas con sobrevivientes conjuntos en las tres tasas.
- **C. Tasas:** 2,5, 5 y 6.
- **D. Cristaloide:** los 12 puntos de §2. Entra sólo en L2 y depende de la decisión sobre τ.
- **E. Extracción de O2:** ρ con banda 2,0–3,0. Como el lactato, D, el déficit y la adecuación no dependen de ρ, se
  simula sólo con 2,5 y no se multiplica nada por ρ. Que ρ tampoco mueve la hemodinámica no está persistido: la
  revisión lo sondeó (0,0) y el diseño no depende de ello.
- **F. Modificadores de L3:** fijos (0,8 y 0,1).
- **G. Parámetros propios del lactato:**
  - **Explorados:** τ de la deuda 30/60/120; ganancia 2/6/12; τ del lactato 45/120/240; exceso de llegada
    inferior/medio/superior; y los 5 pares (deuda, entrega) de llegada.
  - **Con sensibilidad sólo sobre los sobrevivientes:** la deuda por déficit y la demanda basal.
  - **Fuera:** la frecuencia intrínseca.
- **Recuentos antes de simular:**
  - candidatos: de 1 754 460 a 14 171 760;
  - trayectorias hemodinámicas únicas, las únicas simulaciones del núcleo: de 2308 a 14 256, con 405 posprocesos por
    trayectoria;
  - producto ingenuo: de 94,7 a 765 millones de simulaciones;
  - simulaciones evitadas: entre 94,7 y 765 millones.
- **Diseño factorizado, en orden:**
  1. Enumerar P1 y P3 una vez.
  2. Simular por caso L1 (P1), L2 (P1 × D) y L3 (P3), una vez cada uno: la hemodinámica no depende del nivel de
     entrega de llegada ni de la cinética de la deuda o del lactato (persistido), y lo que leen las FD-LAC tampoco
     depende de ρ.
  3. Calcular el déficit de los 3 niveles de entrega como posproceso.
  4. Calcular D y el lactato como posproceso, con la recursión del núcleo, para los 5 pares de llegada × 81
     combinaciones de cinética y exceso.
  5. Validar el posproceso contra corridas completas en una muestra pequeña, antes de usarlo.
  6. Aplicar las FD-LAC en secuencia (L1 primero; L2 y L3 sólo para lo que sobrevive), con la adecuación = déficit 0.
  7. Correr la sensibilidad sólo sobre los sobrevivientes.

## 8. Persistencia de las dos comprobaciones de la revisión (P2I-2AA-8)

- **«ρ no altera la hemodinámica»:** no hace falta persistirla. Ninguna conclusión comprometida depende de ella: las
  FD-LAC leen el lactato y la adecuación, y las dos son invariantes ante ρ en registros comprometidos:
  - D y el lactato, en P2I-2Z;
  - el déficit y la adecuación, en este paquete.
- **«La sustitución de D no omite claves»:** sí era material, porque la completitud de A depende de ella. Ahora está
  en el registro congelado (387 claves, cada una con su testigo), y una prueba recalcula en vivo algunos testigos.

## 9. Recongelamiento por la revisión y ejecución en el HEAD final

- **Historia:**
  - congelamiento en `83996c5`;
  - corrida y commit ejecutable en `3a9aa10`, con la suite completa verde sobre ese SHA;
  - la revisión adversarial probó que el código congelado omitía, para la tasa 2,5, los sobrevivientes de las cajas
    de P2I-2W dentro de la banda;
  - recongelamiento en `0b90ddf`: sólo esas claves y ese soporte, más tres detalles de código (la monotonía también
    sobre la dilución a los 120′, todas las columnas en la comprobación del nivel de entrega y un docstring mal
    ubicado);
  - nueva corrida y nuevo commit ejecutable.
- **Resultado de la nueva corrida:**
  - todo lo de τ es idéntico a la primera: diseño, veredictos, región, bordes, límite, trayectorias y clasificación
    práctica;
  - cambian el soporte de la 2,5, sus claves, la completitud y los recuentos del espacio;
  - el veredicto no cambia.
- **Entrega en dos commits:** uno ejecutable (código, pruebas, JSON e informes), sobre el que corre la suite completa,
  y uno posterior sólo de documentación, si hace falta. La equivalencia del árbol ejecutable se prueba con el diff
  entre los dos.

## 10. Qué no hace

- **Restricciones:** no cambia ninguna, ni el criterio robusto, la muestra de sangre o el escenario de infusión
  (`blood_constraints.py` idéntico byte a byte).
- **τ:** no agrega valores por encima de 240, ni otro F0 o Finf.
- **Aprobaciones:** no aprueba, no elige y no interpola ningún parámetro.
- **Lactato:** no ejecuta el filtro y no aplica la semántica de la adecuación a ninguna restricción.
- **L3:** no calibra los modificadores ni inventa rangos.
- **Otros límites:** no calibra la presión ni la FC, no activa el colapso, no migra ni integra nada. TD-88 y TD-89
  siguen abiertas.

## 11. Decisiones pendientes (docencia)

- **τ con Finf 0,05**, para destrabar la preparación: aceptar τ ≤ 240 con la cota de FD-BLD-05 declarada más allá,
  autorizar un valor más, o tratar Finf y τ como una sola curva de lo retenido.
- **Relleno de la tasa 2,5:** con P2I-2W, su soporte incluye la meta 1,0 y τ 480. Las cajas con τ 960 no dejaron
  sobrevivientes. No queda nada pendiente de extender.
- **Vecinos de Finf con τ ≥ 90:** si se elige la opción de una sola curva Finf–τ, qué hacer con Finf 0 y 0,15, que no
  se probaron.
- **FD-24 y FD-25** (modificadores de L3): siguen abiertas.
