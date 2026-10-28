# P2I-2W · Extensión de los bordes abiertos de la cuadrícula y auditoría semántica del arnés

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución, no migra GI ni otra familia, no refiltra el lactato (P2I-2R sigue en pausa);
- no calibra la presión ni la FC, ni activa el colapso;
- no se ajusta al motor heredado y no elige ningún conjunto final de parámetros ocultos;
- no cambia ninguna restricción docente: usa exactamente las de P2I-2V-R.

Código: `clinical_core/blood_extension.py` (regla, puntos, diseño, política y evaluación; congelado antes de evaluar)
y `clinical_core/blood_extension_report.py` (sólo este informe). Números: `docs/revision/P2I2W_blood_extension.json`.
Registro de partida: `docs/revision/P2I2VR_RESTRICCIONES_REVISADAS_FILTRO.md` (P2I-2V-R, cerrado, `a9ab10d8…`).

**Ampliado por P2I-2X (2026-10-28).** P2I-2W quedó aceptado y cerrado. Este documento es su registro, tal como corrió
con el congelamiento `5257b233…`, y ya no se regenera. P2I-2X aplica la compatibilidad con la verdad del caso a las
posiciones 0,65 / 0,75, densifica la tasa común entre 5 y 10 y amplía la taxonomía de bordes:
`docs/revision/P2I2X_CIERRE_BORDES_TASA.md`.

## 1. Encargo docente (2026-10-27)

- P2I-2V-R queda aceptado y cerrado: con la tasa común sobreviven 4896 candidatos.
- La región toca el borde superior de la cuadrícula en varios parámetros. La docencia autoriza una extensión LIMITADA
  para saber si esos parámetros los acota la fisiología o sólo los trunca la cuadrícula.
- Sólo se extienden las dimensiones que el informe de P2I-2V-R señaló abiertas en el borde, y sólo por su lado
  abierto, con puntos declarados y congelados antes de evaluar. Sin barrido cartesiano completo.
- El estado de borde se informa aparte de la identificabilidad.
- Auditoría semántica de las comprobaciones de nivel 1 que escriben V directamente.
- Las sondas históricas de bolo siguen siendo históricas.

## 2. Regla de extensión, puntos y diseño (congelados antes de evaluar)

<!-- generado:regla -->
Congelamiento de P2I-2W: `5257b2336caa76819bdc1f5f3a946dc440dbff88c9e101d9ed25c38287772f6e`, con un commit hecho antes de evaluar ningún candidato extendido (una prueba lo fija). Registro de partida: el filtro de P2I-2V-R, `a9ab10d8d809070e5e76bcb4557525924dcb918fbd86d9b2a62393687d53c893`.

| Dimensión abierta en P2I-2V-R | Explorados | Sobreviven | Lado abierto | Espaciado | Paso | Puntos de extensión | Descartados (fuera del dominio) |
|---|---|---|---|---|---|---|---|
| tasa de sangrado común (mL-eq/min) | 1,25, 2,5, 5 | 2,5, 5 | superior | razón constante | × 2 | 10, 20 | — |
| fracción retenida del cristaloide | 0,125, 0,2, 0,3 | 0,2, 0,3 | superior | AMBIGUO | — | — | — |
| meta del relleno (fracción de lo perdido) | 0,25, 0,5, 0,75 | 0,5, 0,75 | superior | diferencia constante | + 0,25 | 1 | 1,25 |
| τ del relleno (min) | 60, 120, 240 | 120, 240 | superior | razón constante | × 2 | 480, 960 | — |
| posición de precarga de llegada (57m) | 0,2, 0,35, 0,5 | 0,5 | superior | diferencia constante | + 0,15 | 0,65, 0,8 | — |
| posición de precarga de llegada (72f) | 0,3, 0,45, 0,6 | 0,6 | superior | diferencia constante | + 0,15 | 0,75, 0,9 | — |

**fracción retenida del cristaloide: continuación AMBIGUA, sin extender.** Los valores explorados (0,125, 0,2, 0,3) no tienen una diferencia ni una razón constantes. Las dos continuaciones simples dan valores distintos (por la última diferencia: 0,4, 0,5; por la última razón: 0,45, 0,675). No se eligió ninguna ni se evaluó: queda para una decisión docente.

| Parte del diseño | Cajas | Candidatos |
|---|---|---|
| caja superviviente (P2I-2V-R) | 1 | 104976 |
| un punto a la vez | 9 | 682344 |
| pares | 32 | 1679616 |
| esquina de los primeros pasos | 1 | 13122 |
| **extendidos (sin la caja superviviente)** | 42 | 2375082 |

Pares combinados y por qué:

- tasa de sangrado común (mL-eq/min) × meta del relleno (fracción de lo perdido): las leen a la vez: FD-BLD-06, FD-BLD-08, U-HB, U-OUT.
- tasa de sangrado común (mL-eq/min) × τ del relleno (min): las leen a la vez: FD-BLD-06, FD-BLD-08, U-HB, U-OUT.
- tasa de sangrado común (mL-eq/min) × posición de precarga de llegada (57m): las leen a la vez: U-OUT.
- tasa de sangrado común (mL-eq/min) × posición de precarga de llegada (72f): las leen a la vez: U-OUT.
- meta del relleno (fracción de lo perdido) × τ del relleno (min): las leen a la vez: FD-BLD-06, FD-BLD-07, FD-BLD-08, FD-BLD-09, U-HB, U-OUT.
- meta del relleno (fracción de lo perdido) × posición de precarga de llegada (57m): las leen a la vez: U-OUT.
- meta del relleno (fracción de lo perdido) × posición de precarga de llegada (72f): las leen a la vez: U-OUT.
- τ del relleno (min) × posición de precarga de llegada (57m): las leen a la vez: U-OUT.
- τ del relleno (min) × posición de precarga de llegada (72f): las leen a la vez: U-OUT.
- posición de precarga de llegada (57m) × posición de precarga de llegada (72f): ninguna restricción las lee a la vez (cada caso se lee solo); el sobreviviente conjunto necesita ambos.
<!-- /generado:regla -->

- **Orden.** Los puntos, el diseño y la política se congelaron y comprometieron (commit `6a0d3b8`) antes de evaluar
  ningún candidato extendido. Antes del congelamiento sólo se evaluó la caja superviviente de P2I-2V-R, ya conocida,
  para comprobar que el evaluador reproduce sus 4896 sobrevivientes.
- **Tamaño.** 43 cajas disjuntas: la superviviente y 42 con algún punto extendido, que suman 2 375 082 candidatos
  extendidos, menos del 5 % del producto cartesiano de la cuadrícula extendida (49 207 500). Las demás dimensiones conservan sólo los valores que sobreviven en P2I-2V-R; no se
  vuelve a explorar ningún valor ya rechazado.
- **Lectura primaria.** Una tasa común para los dos casos.
- **Sensibilidad.** Las columnas de cada caso por separado dicen qué tolera cada caso con su propia tasa. No son el
  recuento conjunto V8 de P2I-2V-R.
- **Pares.** El criterio («alguna restricción lee las dos, o el sobreviviente conjunto necesita las dos posiciones»)
  admitió los diez pares posibles.

## 3. Resultado de la extensión

<!-- generado:extension -->
La caja superviviente reproduce el filtro congelado: 4896 sobrevivientes con la tasa común, los mismos de P2I-2V-R (la corrida se detiene si no). Filas ilegibles: 5514. Contradicciones en las comprobaciones cruzadas: 0.

### Resultado por caja

Sobreviviente conjunto: tasa común (lectura primaria). «Sólo 57m» y «sólo 72f»: cada caso por separado, como sensibilidad (qué tolera cada caso con su propia tasa; no es el recuento conjunto V8 de P2I-2V-R); entre paréntesis, los candidatos de ese caso que quedan ILEGIBLES (ninguna restricción legible falla, pero alguna no se puede leer), que no son un rechazo. «Ilegibles»: candidatos conjuntos ilegibles. Rechazos: cuántos candidatos falla cada restricción en algún caso (entre paréntesis, en cuántos es la única que falla).

| Caja | Candidatos | Sobreviven | Sólo 57m | Sólo 72f | Ilegibles | Rechazos |
|---|---|---|---|---|---|---|
| caja superviviente | 104976 | 4896 | 5004 | 7182 | 0 | U-OUT 68526 (sola 7164) · FD-BLD-05 52488 (sola 3258) · FD-BLD-07 52488 (sola 3522) · FD-BLD-01 38880 (sola 2475) · FD-BLD-06 31104 (sola 1179) · FD-BLD-02 11664 (sola 774) · FD-BLD-04 11664 |
| tasa de sangrado común (mL-eq/min) = 10 | 52488 | 0 | 0 | 0 | 0 | U-OUT 52488 (sola 6372) · FD-BLD-05 26244 · FD-BLD-07 26244 · FD-BLD-01 19440 · FD-BLD-06 13689 · FD-BLD-02 5832 · FD-BLD-04 5832 · U-HB 1458 |
| tasa de sangrado común (mL-eq/min) = 20 | 52488 | 0 | 0 | 0 | 0 | U-OUT 52488 (sola 7452) · FD-BLD-05 26244 · FD-BLD-07 26244 · FD-BLD-01 19440 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| meta del relleno (fracción de lo perdido) = 1 | 52488 | 663 | 675 | 1197 | 0 | FD-BLD-07 43740 (sola 2538) · U-OUT 37908 (sola 1461) · FD-BLD-05 26244 (sola 420) · FD-BLD-01 19440 (sola 327) · FD-BLD-06 15066 (sola 120) · FD-BLD-02 5832 (sola 135) · FD-BLD-04 5832 |
| τ del relleno (min) = 480 | 52488 | 0 | 0 | 0 | 0 | FD-BLD-07 52488 (sola 4536) · U-OUT 34992 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 15066 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| τ del relleno (min) = 960 | 52488 | 0 | 0 | 0 | 0 | FD-BLD-07 52488 (sola 4536) · U-OUT 34992 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 14580 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| posición de precarga de llegada (57m) = 0,65 | 104976 | 0 | 2340 | 7182 | 0 | U-OUT 104976 (sola 13608) · FD-BLD-05 52488 · FD-BLD-07 52488 · FD-BLD-01 38880 · FD-BLD-06 31104 · FD-BLD-04 11664 |
| posición de precarga de llegada (57m) = 0,8 | 104976 | 0 | 0 | 7182 | 0 | U-OUT 104976 (sola 13608) · FD-BLD-05 52488 · FD-BLD-07 52488 · FD-BLD-01 38880 · FD-BLD-06 31104 · FD-BLD-04 11664 |
| posición de precarga de llegada (72f) = 0,75 | 104976 | 0 | 5004 | 2394 | 0 | U-OUT 104976 (sola 12060) · FD-BLD-05 52488 · FD-BLD-07 52488 · FD-BLD-01 38880 · FD-BLD-06 31104 · FD-BLD-02 11664 · FD-BLD-04 11664 |
| posición de precarga de llegada (72f) = 0,9 | 104976 | 0 | 5004 | 0 | 0 | U-OUT 104976 (sola 12060) · FD-BLD-05 52488 · FD-BLD-07 52488 · FD-BLD-01 38880 · FD-BLD-06 31104 · FD-BLD-02 11664 · FD-BLD-04 11664 |
| tasa de sangrado común (mL-eq/min) = 10 · meta del relleno (fracción de lo perdido) = 1 | 26244 | 0 | 0 | 0 | 0 | U-OUT 26244 (sola 1062) · FD-BLD-07 21870 · FD-BLD-05 13122 · FD-BLD-01 9720 · FD-BLD-06 6804 · FD-BLD-02 2916 · FD-BLD-04 2916 · U-HB 2916 |
| tasa de sangrado común (mL-eq/min) = 20 · meta del relleno (fracción de lo perdido) = 1 | 26244 | 0 | 0 | 0 | 0 | U-OUT 26244 (sola 1242) · FD-BLD-07 21870 · FD-BLD-05 13122 · FD-BLD-01 9720 · FD-BLD-02 2916 · FD-BLD-04 2916 |
| tasa de sangrado común (mL-eq/min) = 10 · τ del relleno (min) = 480 | 26244 | 0 | 0 | 0 | 0 | FD-BLD-07 26244 · U-OUT 26244 · FD-BLD-05 13122 · FD-BLD-01 9720 · FD-BLD-06 4536 · FD-BLD-02 2916 · FD-BLD-04 2916 |
| tasa de sangrado común (mL-eq/min) = 10 · τ del relleno (min) = 960 | 26244 | 0 | 0 | 0 | 0 | FD-BLD-07 26244 · U-OUT 26244 · FD-BLD-05 13122 · FD-BLD-01 9720 · FD-BLD-06 4536 · FD-BLD-02 2916 · FD-BLD-04 2916 |
| tasa de sangrado común (mL-eq/min) = 20 · τ del relleno (min) = 480 | 26244 | 0 | 0 | 0 | 0 | FD-BLD-07 26244 · U-OUT 26244 · FD-BLD-05 13122 · FD-BLD-01 9720 · FD-BLD-02 2916 · FD-BLD-04 2916 |
| tasa de sangrado común (mL-eq/min) = 20 · τ del relleno (min) = 960 | 26244 | 0 | 0 | 0 | 0 | FD-BLD-07 26244 · U-OUT 26244 · FD-BLD-05 13122 · FD-BLD-01 9720 · FD-BLD-02 2916 · FD-BLD-04 2916 |
| tasa de sangrado común (mL-eq/min) = 10 · posición de precarga de llegada (57m) = 0,65 | 52488 | 0 | 0 (+1944 ilegibles) | 0 | 0 | U-OUT 52488 (sola 7182) · FD-BLD-05 26244 · FD-BLD-07 26244 · FD-BLD-01 19440 · FD-BLD-06 13689 · FD-BLD-04 5832 · U-HB 1458 |
| tasa de sangrado común (mL-eq/min) = 10 · posición de precarga de llegada (57m) = 0,8 | 52488 | 0 | 0 | 0 | 0 | U-OUT 52488 (sola 7182) · FD-BLD-05 26244 · FD-BLD-07 26244 · FD-BLD-01 19440 · FD-BLD-06 13689 · FD-BLD-04 5832 · U-HB 1458 |
| tasa de sangrado común (mL-eq/min) = 20 · posición de precarga de llegada (57m) = 0,65 | 52488 | 0 | 0 | 0 | 0 | U-OUT 52488 (sola 8262) · FD-BLD-05 26244 · FD-BLD-07 26244 · FD-BLD-01 19440 · FD-BLD-04 5832 |
| tasa de sangrado común (mL-eq/min) = 20 · posición de precarga de llegada (57m) = 0,8 | 52488 | 0 | 0 | 0 | 0 | U-OUT 52488 (sola 8262) · FD-BLD-05 26244 · FD-BLD-07 26244 · FD-BLD-01 19440 · FD-BLD-04 5832 |
| tasa de sangrado común (mL-eq/min) = 10 · posición de precarga de llegada (72f) = 0,75 | 52488 | 0 | 0 | 2394 | 0 | U-OUT 52488 (sola 6372) · FD-BLD-05 26244 · FD-BLD-07 26244 · FD-BLD-01 19440 · FD-BLD-06 13689 · FD-BLD-02 5832 · FD-BLD-04 5832 · U-HB 1458 |
| tasa de sangrado común (mL-eq/min) = 10 · posición de precarga de llegada (72f) = 0,9 | 52488 | 0 | 0 | 2394 | 0 | U-OUT 52488 (sola 6372) · FD-BLD-05 26244 · FD-BLD-07 26244 · FD-BLD-01 19440 · FD-BLD-06 13689 · FD-BLD-02 5832 · FD-BLD-04 5832 · U-HB 1458 |
| tasa de sangrado común (mL-eq/min) = 20 · posición de precarga de llegada (72f) = 0,75 | 52488 | 0 | 0 | 0 | 0 | U-OUT 52488 (sola 7452) · FD-BLD-05 26244 · FD-BLD-07 26244 · FD-BLD-01 19440 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| tasa de sangrado común (mL-eq/min) = 20 · posición de precarga de llegada (72f) = 0,9 | 52488 | 0 | 0 | 0 (+1836 ilegibles) | 0 | U-OUT 52488 (sola 7452) · FD-BLD-05 26244 · FD-BLD-07 26244 · FD-BLD-01 19440 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| meta del relleno (fracción de lo perdido) = 1 · τ del relleno (min) = 480 | 26244 | 1512 | 1560 | 2394 | 0 | U-OUT 17496 (sola 2508) · FD-BLD-05 13122 (sola 984) · FD-BLD-01 9720 (sola 756) · FD-BLD-07 8748 (sola 756) · FD-BLD-06 7776 (sola 324) · FD-BLD-02 2916 · FD-BLD-04 2916 |
| meta del relleno (fracción de lo perdido) = 1 · τ del relleno (min) = 960 | 26244 | 0 | 0 | 0 | 0 | FD-BLD-07 26244 (sola 2268) · U-OUT 17496 · FD-BLD-05 13122 · FD-BLD-01 9720 · FD-BLD-06 7533 · FD-BLD-02 2916 · FD-BLD-04 2916 |
| meta del relleno (fracción de lo perdido) = 1 · posición de precarga de llegada (57m) = 0,65 | 52488 | 0 | 411 | 1197 | 0 | U-OUT 52488 (sola 2394) · FD-BLD-07 43740 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 15066 · FD-BLD-04 5832 |
| meta del relleno (fracción de lo perdido) = 1 · posición de precarga de llegada (57m) = 0,8 | 52488 | 0 | 0 | 1197 | 0 | U-OUT 52488 (sola 2394) · FD-BLD-07 43740 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 15066 · FD-BLD-04 5832 |
| meta del relleno (fracción de lo perdido) = 1 · posición de precarga de llegada (72f) = 0,75 | 52488 | 0 | 675 | 399 | 0 | U-OUT 52488 (sola 2124) · FD-BLD-07 43740 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 15066 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| meta del relleno (fracción de lo perdido) = 1 · posición de precarga de llegada (72f) = 0,9 | 52488 | 0 | 675 | 0 | 0 | U-OUT 52488 (sola 2124) · FD-BLD-07 43740 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 15066 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| τ del relleno (min) = 480 · posición de precarga de llegada (57m) = 0,65 | 52488 | 0 | 0 | 0 | 0 | FD-BLD-07 52488 · U-OUT 52488 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 15066 · FD-BLD-04 5832 |
| τ del relleno (min) = 480 · posición de precarga de llegada (57m) = 0,8 | 52488 | 0 | 0 | 0 | 0 | FD-BLD-07 52488 · U-OUT 52488 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 15066 · FD-BLD-04 5832 |
| τ del relleno (min) = 960 · posición de precarga de llegada (57m) = 0,65 | 52488 | 0 | 0 | 0 | 0 | FD-BLD-07 52488 · U-OUT 52488 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 14580 · FD-BLD-04 5832 |
| τ del relleno (min) = 960 · posición de precarga de llegada (57m) = 0,8 | 52488 | 0 | 0 | 0 | 0 | FD-BLD-07 52488 · U-OUT 52488 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 14580 · FD-BLD-04 5832 |
| τ del relleno (min) = 480 · posición de precarga de llegada (72f) = 0,75 | 52488 | 0 | 0 | 0 | 0 | FD-BLD-07 52488 · U-OUT 52488 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 15066 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| τ del relleno (min) = 480 · posición de precarga de llegada (72f) = 0,9 | 52488 | 0 | 0 | 0 | 0 | FD-BLD-07 52488 · U-OUT 52488 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 15066 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| τ del relleno (min) = 960 · posición de precarga de llegada (72f) = 0,75 | 52488 | 0 | 0 | 0 | 0 | FD-BLD-07 52488 · U-OUT 52488 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 14580 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| τ del relleno (min) = 960 · posición de precarga de llegada (72f) = 0,9 | 52488 | 0 | 0 | 0 | 0 | FD-BLD-07 52488 · U-OUT 52488 · FD-BLD-05 26244 · FD-BLD-01 19440 · FD-BLD-06 14580 · FD-BLD-02 5832 · FD-BLD-04 5832 |
| posición de precarga de llegada (57m) = 0,65 · posición de precarga de llegada (72f) = 0,75 | 104976 | 2268 | 2340 | 2394 | 0 | U-OUT 87480 (sola 11340) · FD-BLD-05 52488 (sola 1476) · FD-BLD-07 52488 (sola 2268) · FD-BLD-01 38880 (sola 1134) · FD-BLD-06 31104 (sola 486) · FD-BLD-04 11664 |
| posición de precarga de llegada (57m) = 0,65 · posición de precarga de llegada (72f) = 0,9 | 104976 | 0 | 2340 | 0 | 0 | U-OUT 104976 (sola 13608) · FD-BLD-05 52488 · FD-BLD-07 52488 · FD-BLD-01 38880 · FD-BLD-06 31104 · FD-BLD-04 11664 |
| posición de precarga de llegada (57m) = 0,8 · posición de precarga de llegada (72f) = 0,75 | 104976 | 0 | 0 | 2394 | 0 | U-OUT 104976 (sola 13608) · FD-BLD-05 52488 · FD-BLD-07 52488 · FD-BLD-01 38880 · FD-BLD-06 31104 · FD-BLD-04 11664 |
| posición de precarga de llegada (57m) = 0,8 · posición de precarga de llegada (72f) = 0,9 | 104976 | 0 | 0 | 0 | 0 | U-OUT 104976 (sola 13608) · FD-BLD-05 52488 · FD-BLD-07 52488 · FD-BLD-01 38880 · FD-BLD-06 31104 · FD-BLD-04 11664 |
| tasa de sangrado común (mL-eq/min) = 10 · meta del relleno (fracción de lo perdido) = 1 · τ del relleno (min) = 480 · posición de precarga de llegada (57m) = 0,65 · posición de precarga de llegada (72f) = 0,75 | 13122 | 0 | 0 | 798 | 0 | U-OUT 13122 (sola 2394) · FD-BLD-05 6561 · FD-BLD-01 4860 · FD-BLD-07 4374 · FD-BLD-06 2268 · FD-BLD-04 1458 |

### Dónde salen de su envolvente U-OUT, U-HB y FD-BLD-07 (un punto a la vez)

Filas distintas que fallan, por minuto y lado («bajo»: por debajo del mínimo; «sobre»: por encima del máximo).

| Caja | Detalle |
|---|---|
| tasa de sangrado común (mL-eq/min) = 10 | 57m FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 57m U-OUT: 120:bajo (324), 30:bajo (324), 60:bajo (324); 72f FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 72f U-HB: 120:sobre (1); 72f U-OUT: 120:bajo (324), 30:bajo (324), 60:bajo (324) |
| tasa de sangrado común (mL-eq/min) = 20 | 57m FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 57m U-OUT: 120:bajo (324), 30:bajo (324), 60:bajo (324); 72f FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 72f U-OUT: 120:bajo (324), 30:bajo (324), 60:bajo (324) |
| meta del relleno (fracción de lo perdido) = 1 | 57m FD-BLD-07: 120:sobre (6), 120:bajo (3), 240:sobre (12), 60:sobre (6); 57m U-OUT: 120:sobre (117), 120:bajo (117), 30:sobre (54), 30:bajo (108), 60:sobre (54), 60:bajo (108); 72f FD-BLD-07: 120:sobre (6), 120:bajo (3), 240:sobre (12), 60:sobre (6); 72f U-OUT: 120:sobre (108), 120:bajo (90), 30:bajo (108), 60:sobre (54), 60:bajo (108) |
| τ del relleno (min) = 480 | 57m FD-BLD-07: 120:bajo (18), 240:bajo (18), 60:bajo (18); 57m U-OUT: 120:sobre (54), 120:bajo (162), 30:bajo (108), 60:sobre (54), 60:bajo (108); 72f FD-BLD-07: 120:bajo (18), 240:bajo (18), 60:bajo (18); 72f U-OUT: 120:sobre (54), 120:bajo (144), 30:bajo (108), 60:sobre (54), 60:bajo (108) |
| τ del relleno (min) = 960 | 57m FD-BLD-07: 120:bajo (18), 240:bajo (18), 60:bajo (18); 57m U-OUT: 120:sobre (54), 120:bajo (162), 30:bajo (108), 60:sobre (54), 60:bajo (108); 72f FD-BLD-07: 120:bajo (18), 240:bajo (18), 60:bajo (18); 72f U-OUT: 120:sobre (54), 120:bajo (162), 30:bajo (108), 60:sobre (54), 60:bajo (108) |
| posición de precarga de llegada (57m) = 0,65 | 57m FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 57m U-OUT: 120:sobre (432), 120:bajo (108), 30:sobre (216), 60:sobre (432), 60:bajo (90); 72f FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 72f U-OUT: 120:sobre (126), 120:bajo (216), 30:bajo (216), 60:sobre (108), 60:bajo (216) |
| posición de precarga de llegada (57m) = 0,8 | 57m FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 57m U-OUT: 120:sobre (594), 30:sobre (540), 60:sobre (612); 72f FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 72f U-OUT: 120:sobre (126), 120:bajo (216), 30:bajo (216), 60:sobre (108), 60:bajo (216) |
| posición de precarga de llegada (72f) = 0,75 | 57m FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 57m U-OUT: 120:sobre (171), 120:bajo (252), 30:sobre (108), 30:bajo (216), 60:sobre (108), 60:bajo (216); 72f FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 72f U-OUT: 120:sobre (432), 120:bajo (90), 30:sobre (108), 60:sobre (351), 60:bajo (36) |
| posición de precarga de llegada (72f) = 0,9 | 57m FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 57m U-OUT: 120:sobre (171), 120:bajo (252), 30:sobre (108), 30:bajo (216), 60:sobre (108), 60:bajo (216); 72f FD-BLD-07: 120:sobre (6), 120:bajo (12), 240:sobre (6), 60:sobre (6); 72f U-OUT: 120:sobre (648), 30:sobre (459), 60:sobre (648) |

### Lo que leen las restricciones en cada punto (filas de su caja; contexto, nada se ajusta)

| Punto | Caso | Gasto sin tratar 30′ / 60′ / 120′ | Caída de Hb 60′ / 120′ | Relleno 60′ / 120′ / 240′ | 1 U: Δ gasto | 2.ª U: Δ gasto | Dilución pico 1 L |
|---|---|---|---|---|---|---|---|
| tasa de sangrado común (mL-eq/min) = 10 | 57m | 0,37–0,80 / 0,00–0,60 / 0,00–0,21 | 0,07–0,24 / 0,29–0,87 | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,15–0,44 | 0,11–0,17 | 0,17–0,57 |
| tasa de sangrado común (mL-eq/min) = 10 | 72f | 0,58–0,87 / 0,00–0,73 / 0,00–0,47 | 0,03–0,22 / 0,05–0,83 | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,10–0,29 | 0,08–0,13 | 0,16–0,56 |
| tasa de sangrado común (mL-eq/min) = 20 | 57m | 0,00–0,56 / 0,00–0,04 / 0,00–0,00 | — / — | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,15–0,44 | 0,11–0,17 | — |
| tasa de sangrado común (mL-eq/min) = 20 | 72f | 0,00–0,70 / 0,00–0,36 / 0,00–0,00 | — / — | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,10–0,29 | 0,08–0,13 | — |
| meta del relleno (fracción de lo perdido) = 1 | 57m | 0,73–0,95 / 0,40–0,92 / 0,00–0,86 | 0,02–0,15 / 0,05–0,52 | 0,11–0,36 / 0,19–0,61 / 0,31–0,86 | 0,15–0,44 | 0,11–0,17 | 0,16–0,57 |
| meta del relleno (fracción de lo perdido) = 1 | 72f | 0,82–0,97 / 0,60–0,95 / 0,00–0,91 | 0,02–0,14 / 0,04–0,50 | 0,11–0,36 / 0,19–0,61 / 0,31–0,86 | 0,10–0,29 | 0,08–0,13 | 0,15–0,55 |
| τ del relleno (min) = 480 | 57m | 0,72–0,95 / 0,37–0,90 / 0,00–0,80 | 0,01–0,03 / 0,02–0,13 | 0,05–0,08 / 0,11–0,16 / 0,19–0,29 | 0,15–0,44 | 0,11–0,17 | 0,16–0,58 |
| τ del relleno (min) = 480 | 72f | 0,81–0,97 / 0,58–0,93 / 0,00–0,87 | 0,01–0,03 / 0,02–0,12 | 0,05–0,08 / 0,11–0,16 / 0,19–0,29 | 0,10–0,29 | 0,08–0,13 | 0,16–0,55 |
| τ del relleno (min) = 960 | 57m | 0,72–0,95 / 0,36–0,90 / 0,00–0,79 | 0,00–0,02 / 0,01–0,07 | 0,03–0,04 / 0,06–0,08 / 0,11–0,16 | 0,15–0,44 | 0,11–0,17 | 0,16–0,58 |
| τ del relleno (min) = 960 | 72f | 0,81–0,97 / 0,57–0,93 / 0,00–0,86 | 0,00–0,02 / 0,01–0,07 | 0,03–0,04 / 0,06–0,08 / 0,11–0,16 | 0,10–0,29 | 0,08–0,13 | 0,16–0,56 |
| posición de precarga de llegada (57m) = 0,65 | 57m | 0,85–0,97 / 0,67–0,95 / 0,16–0,92 | 0,01–0,11 / 0,04–0,40 | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,08–0,24 | 0,06–0,11 | 0,16–0,58 |
| posición de precarga de llegada (57m) = 0,65 | 72f | 0,82–0,97 / 0,59–0,94 / 0,00–0,90 | 0,01–0,11 / 0,04–0,38 | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,10–0,29 | 0,08–0,13 | 0,15–0,55 |
| posición de precarga de llegada (57m) = 0,8 | 57m | 0,93–0,99 / 0,85–0,98 / 0,61–0,96 | 0,01–0,11 / 0,04–0,40 | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,04–0,11 | 0,03–0,06 | 0,16–0,58 |
| posición de precarga de llegada (57m) = 0,8 | 72f | 0,82–0,97 / 0,59–0,94 / 0,00–0,90 | 0,01–0,11 / 0,04–0,38 | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,10–0,29 | 0,08–0,13 | 0,15–0,55 |
| posición de precarga de llegada (72f) = 0,75 | 57m | 0,73–0,95 / 0,39–0,91 / 0,00–0,84 | 0,01–0,11 / 0,04–0,40 | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,15–0,44 | 0,11–0,17 | 0,16–0,58 |
| posición de precarga de llegada (72f) = 0,75 | 72f | 0,91–0,98 / 0,80–0,97 / 0,48–0,95 | 0,01–0,11 / 0,04–0,38 | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,05–0,15 | 0,04–0,07 | 0,15–0,55 |
| posición de precarga de llegada (72f) = 0,9 | 57m | 0,73–0,95 / 0,39–0,91 / 0,00–0,84 | 0,01–0,11 / 0,04–0,40 | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,15–0,44 | 0,11–0,17 | 0,16–0,58 |
| posición de precarga de llegada (72f) = 0,9 | 72f | 0,97–0,99 / 0,93–0,99 / 0,83–0,98 | 0,01–0,11 / 0,04–0,38 | 0,10–0,27 / 0,19–0,46 / 0,31–0,64 | 0,02–0,05 | 0,01–0,03 | 0,15–0,55 |

### Identificabilidad y estado de borde, antes y después

Clase: la regla congelada de P2I-2V-R (cuántos valores explorados sobreviven). Borde: si sobrevive el valor explorado más bajo o el más alto. Son dos lecturas distintas: un solo valor superviviente en el borde es WELL_CONSTRAINED por recuento, pero no está identificado.

| Parámetro | Explorados | Sobreviven | Clase antes → después | Borde antes → después | Nota |
|---|---|---|---|---|---|
| tasa de sangrado común (mL-eq/min) | 1,25, 2,5, 5, 10, 20 | 2,5, 5 | PARTIALLY_CONSTRAINED → PARTIALLY_CONSTRAINED | OPEN_UPPER_GRID_EDGE → INTERIOR | extendido: 10, 20 |
| posición de precarga de llegada (57m) | 0,2, 0,35, 0,5, 0,65, 0,8 | 0,5, 0,65 | WELL_CONSTRAINED → PARTIALLY_CONSTRAINED | OPEN_UPPER_GRID_EDGE → INTERIOR | extendido: 0,65, 0,8 |
| posición de precarga de llegada (72f) | 0,3, 0,45, 0,6, 0,75, 0,9 | 0,6, 0,75 | WELL_CONSTRAINED → PARTIALLY_CONSTRAINED | OPEN_UPPER_GRID_EDGE → INTERIOR | extendido: 0,75, 0,9 |
| B0 (mL-eq) | 3000, 4000, 5000 | 3000, 4000, 5000 | POORLY_IDENTIFIED → POORLY_IDENTIFIED | OPEN_BOTH_GRID_EDGES → OPEN_BOTH_GRID_EDGES | no señalado abierto en P2I-2V-R: sin extender |
| λ/κ (mL-eq) | 600, 833, 1500 | 600, 833, 1500 | POORLY_IDENTIFIED → POORLY_IDENTIFIED | OPEN_BOTH_GRID_EDGES → OPEN_BOTH_GRID_EDGES | no señalado abierto en P2I-2V-R: sin extender |
| meta del relleno (fracción de lo perdido) | 0,25, 0,5, 0,75, 1 | 0,5, 0,75, 1 | PARTIALLY_CONSTRAINED → PARTIALLY_CONSTRAINED | OPEN_UPPER_GRID_EDGE → OPEN_UPPER_GRID_EDGE | extendido: 1; el valor más alto que sobrevive es el límite del dominio |
| τ del relleno (min) | 60, 120, 240, 480, 960 | 120, 240, 480 | PARTIALLY_CONSTRAINED → PARTIALLY_CONSTRAINED | OPEN_UPPER_GRID_EDGE → INTERIOR | extendido: 480, 960 |
| capacidad del relleno (mL-eq) | 100, 500, 1000 | 100, 500, 1000 | POORLY_IDENTIFIED → POORLY_IDENTIFIED | OPEN_BOTH_GRID_EDGES → OPEN_BOTH_GRID_EDGES | no señalado abierto en P2I-2V-R: sin extender |
| contenido de GR de la unidad (Hb, g/dL) | 18, 20, 22 | 18, 20, 22 | POORLY_IDENTIFIED → POORLY_IDENTIFIED | OPEN_BOTH_GRID_EDGES → OPEN_BOTH_GRID_EDGES | no señalado abierto en P2I-2V-R: sin extender |
| volumen de la unidad (mL-eq) | 250, 300, 350 | 250, 300, 350 | POORLY_IDENTIFIED → POORLY_IDENTIFIED | OPEN_BOTH_GRID_EDGES → OPEN_BOTH_GRID_EDGES | no señalado abierto en P2I-2V-R: sin extender |
| fracción retenida del cristaloide | 0,125, 0,2, 0,3 | 0,2, 0,3 | PARTIALLY_CONSTRAINED → PARTIALLY_CONSTRAINED | OPEN_UPPER_GRID_EDGE → OPEN_UPPER_GRID_EDGE | continuación ambigua: sin extender |
| τ de redistribución del cristaloide (min) | 15, 30, 60 | 15, 30, 60 | POORLY_IDENTIFIED → POORLY_IDENTIFIED | OPEN_BOTH_GRID_EDGES → OPEN_BOTH_GRID_EDGES | no señalado abierto en P2I-2V-R: sin extender |
| fracción transitoria del cristaloide | 0,4, 0,6, 0,8 | 0,4, 0,6, 0,8 | POORLY_IDENTIFIED → POORLY_IDENTIFIED | OPEN_BOTH_GRID_EDGES → OPEN_BOTH_GRID_EDGES | no señalado abierto en P2I-2V-R: sin extender |
| ρ (reserva de extracción) | 1, 2,5, 3 | 1, 2,5, 3 | NON_IDENTIFIABLE_SEPARATELY → NON_IDENTIFIABLE_SEPARATELY | OPEN_BOTH_GRID_EDGES → OPEN_BOTH_GRID_EDGES | no señalado abierto en P2I-2V-R: sin extender; sólo ρ × la razón de entrega de llegada llega a D y al déficit; ninguna restricción lo lee |
| κ (por separado) | — | — | NON_IDENTIFIABLE_SEPARATELY | — | sólo λ/κ llega a alguna ancla; la Hb nunca lee κ |
| λ (por separado) | — | — | NON_IDENTIFIABLE_SEPARATELY | — | sólo λ/κ llega a alguna ancla |

### Representativos de P2I-2V-R movidos a cada punto

Los tres representativos de P2I-2V-R (bajo, medio y alto, por su regla congelada), con sólo la coordenada extendida cambiada. Se muestra el medio; la PAS y el lactato son sólo contexto.

**tasa de sangrado común (mL-eq/min) = 10.**

- bajo: 57m: no cumple U-OUT (ilegible: U-HB, FD-BLD-06); 72f: no cumple U-OUT.
- medio: 57m: no cumple U-OUT (ilegible: FD-BLD-06); 72f: no cumple U-OUT.
- alto: 57m: no cumple U-OUT (ilegible: U-HB, FD-BLD-06); 72f: no cumple U-OUT.

| 57m · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,075 | -0,149 | -0,294 |
| Hb (g/dL) | 6,70 | 6,68 | 6,61 | 6,32 |
| volumen circulante C (mL-eq) | 0 | -287 | -549 | -1010 |
| precarga (posición) | 0,50 | 0,39 | 0,28 | 0,02 |
| gasto relativo | 1,00 | 0,79 | 0,56 | 0,04 |
| DO2 | 0,34 | 0,27 | 0,19 | 0,01 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,33 | 0,53 | 0,97 |
| relleno acumulado (mL-eq) | 0 | 13 | 51 | 190 |
| PAS (sólo contexto) | 88 | 79 | 68 | 5 |
| lactato (sólo contexto) | 4,4 | 4,1 | 3,8 | 3,8 |

| 57m · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,049 | -0,073 | -0,145 | -0,286 |
| Hb (g/dL) | 6,70 | 6,39 | 6,41 | 6,40 | 6,19 |
| volumen circulante C (mL-eq) | 0 | -13 | -121 | -417 | -911 |
| precarga (posición) | 0,50 | 0,50 | 0,46 | 0,34 | 0,08 |
| gasto relativo | 1,00 | 0,99 | 0,92 | 0,68 | 0,16 |
| DO2 | 0,34 | 0,32 | 0,30 | 0,22 | 0,05 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,20 | 0,26 | 0,45 | 0,87 |
| relleno acumulado (mL-eq) | 0 | 6 | 13 | 51 | 190 |
| PAS (sólo contexto) | 88 | 88 | 84 | 74 | 22 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,7 |

| 57m · Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,147 | -0,147 | -0,147 |
| Hb (g/dL) | 6,70 | 6,61 | 6,44 | 6,23 |
| volumen circulante C (mL-eq) | 0 | -539 | -452 | -332 |
| precarga (posición) | 0,50 | 0,28 | 0,32 | 0,38 |
| gasto relativo | 1,00 | 0,57 | 0,65 | 0,75 |
| DO2 | 0,34 | 0,19 | 0,21 | 0,24 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,52 | 0,47 | 0,41 |
| relleno acumulado (mL-eq) | 0 | 51 | 138 | 258 |
| PAS (sólo contexto) | 88 | 69 | 72 | 77 |
| lactato (sólo contexto) | 4,4 | 3,8 | 3,7 | 3,7 |

| 72f · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,075 | -0,149 | -0,294 |
| Hb (g/dL) | 6,40 | 6,38 | 6,31 | 6,04 |
| volumen circulante C (mL-eq) | 0 | -287 | -549 | -1010 |
| precarga (posición) | 0,60 | 0,52 | 0,42 | 0,22 |
| gasto relativo | 1,00 | 0,86 | 0,71 | 0,36 |
| DO2 | 0,34 | 0,29 | 0,24 | 0,12 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,27 | 0,41 | 0,71 |
| relleno acumulado (mL-eq) | 0 | 13 | 51 | 190 |
| PAS (sólo contexto) | 98 | 92 | 85 | 54 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,2 | 3,2 |

| 72f · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,049 | -0,073 | -0,145 | -0,286 |
| Hb (g/dL) | 6,40 | 6,11 | 6,12 | 6,11 | 5,92 |
| volumen circulante C (mL-eq) | 0 | -13 | -121 | -417 | -911 |
| precarga (posición) | 0,60 | 0,60 | 0,57 | 0,47 | 0,27 |
| gasto relativo | 1,00 | 0,99 | 0,94 | 0,79 | 0,44 |
| DO2 | 0,34 | 0,32 | 0,31 | 0,26 | 0,14 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,19 | 0,23 | 0,36 | 0,65 |
| relleno acumulado (mL-eq) | 0 | 6 | 13 | 51 | 190 |
| PAS (sólo contexto) | 98 | 98 | 95 | 88 | 67 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 3,1 |

| 72f · Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,147 | -0,147 | -0,147 |
| Hb (g/dL) | 6,40 | 6,31 | 6,16 | 5,96 |
| volumen circulante C (mL-eq) | 0 | -539 | -452 | -332 |
| precarga (posición) | 0,60 | 0,43 | 0,46 | 0,50 |
| gasto relativo | 1,00 | 0,71 | 0,77 | 0,83 |
| DO2 | 0,34 | 0,24 | 0,25 | 0,26 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,40 | 0,37 | 0,34 |
| relleno acumulado (mL-eq) | 0 | 51 | 138 | 258 |
| PAS (sólo contexto) | 98 | 85 | 87 | 91 |
| lactato (sólo contexto) | 3,4 | 3,2 | 3,1 | 3,1 |

**tasa de sangrado común (mL-eq/min) = 20.**

- bajo: 57m: no cumple U-OUT (ilegible: U-HB, FD-BLD-06, FD-BLD-08); 72f: no cumple U-OUT (ilegible: U-HB, FD-BLD-06).
- medio: 57m: no cumple U-OUT (ilegible: U-HB, FD-BLD-06, FD-BLD-08); 72f: no cumple U-OUT (ilegible: U-HB, FD-BLD-06).
- alto: 57m: no cumple U-OUT (ilegible: U-HB, FD-BLD-06, FD-BLD-08); 72f: no cumple U-OUT (ilegible: U-HB, FD-BLD-06).

| 57m · Sin tratar (se detiene en el 57′) | 0′ | 30′ |
|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,150 |
| Hb (g/dL) | 6,70 | 6,65 |
| volumen circulante C (mL-eq) | 0 | -574 |
| precarga (posición) | 0,50 | 0,27 |
| gasto relativo | 1,00 | 0,53 |
| DO2 | 0,34 | 0,18 |
| estado de extracción | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,55 |
| relleno acumulado (mL-eq) | 0 | 26 |
| PAS (sólo contexto) | 88 | 67 |
| lactato (sólo contexto) | 4,4 | 4,1 |

| 57m · 1 L en 20 min con sangrado (se detiene en el 65′) | 0′ | 20′ | 30′ | 60′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,098 | -0,145 | -0,287 |
| Hb (g/dL) | 6,70 | 6,38 | 6,38 | 6,29 |
| volumen circulante C (mL-eq) | 0 | -207 | -408 | -966 |
| precarga (posición) | 0,50 | 0,43 | 0,34 | 0,05 |
| gasto relativo | 1,00 | 0,85 | 0,69 | 0,10 |
| DO2 | 0,34 | 0,28 | 0,22 | 0,03 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,31 | 0,44 | 0,92 |
| relleno acumulado (mL-eq) | 0 | 12 | 26 | 102 |
| PAS (sólo contexto) | 88 | 81 | 74 | 13 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,1 | 3,9 |

| 57m · Hemostasia a los 60 min (se detiene en el 57′) | 0′ |
|---|---|
| contenido de GR (cambio relativo) | 0,000 |
| Hb (g/dL) | 6,70 |
| volumen circulante C (mL-eq) | 0 |
| precarga (posición) | 0,50 |
| gasto relativo | 1,00 |
| DO2 | 0,34 |
| estado de extracción | crítica |
| déficit crítico efectivo | 0,15 |
| relleno acumulado (mL-eq) | 0 |
| PAS (sólo contexto) | 88 |
| lactato (sólo contexto) | 4,4 |

| 72f · Sin tratar (se detiene en el 77′) | 0′ | 30′ | 60′ |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,150 | -0,297 |
| Hb (g/dL) | 6,40 | 6,35 | 6,20 |
| volumen circulante C (mL-eq) | 0 | -574 | -1098 |
| precarga (posición) | 0,60 | 0,41 | 0,17 |
| gasto relativo | 1,00 | 0,69 | 0,28 |
| DO2 | 0,34 | 0,23 | 0,09 |
| estado de extracción | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,42 | 0,77 |
| relleno acumulado (mL-eq) | 0 | 26 | 102 |
| PAS (sólo contexto) | 98 | 84 | 42 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 |

| 72f · 1 L en 20 min con sangrado (se detiene en el 84′) | 0′ | 20′ | 30′ | 60′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,098 | -0,145 | -0,287 |
| Hb (g/dL) | 6,40 | 6,09 | 6,09 | 6,01 |
| volumen circulante C (mL-eq) | 0 | -207 | -408 | -966 |
| precarga (posición) | 0,60 | 0,54 | 0,47 | 0,24 |
| gasto relativo | 1,00 | 0,90 | 0,79 | 0,40 |
| DO2 | 0,34 | 0,29 | 0,26 | 0,13 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,27 | 0,36 | 0,68 |
| relleno acumulado (mL-eq) | 0 | 12 | 26 | 102 |
| PAS (sólo contexto) | 98 | 94 | 89 | 60 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,2 |

| 72f · Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,292 | -0,292 | -0,292 |
| Hb (g/dL) | 6,40 | 6,20 | 5,85 | 5,43 |
| volumen circulante C (mL-eq) | 0 | -1078 | -905 | -665 |
| precarga (posición) | 0,60 | 0,18 | 0,27 | 0,38 |
| gasto relativo | 1,00 | 0,30 | 0,45 | 0,63 |
| DO2 | 0,34 | 0,10 | 0,14 | 0,18 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,75 | 0,65 | 0,55 |
| relleno acumulado (mL-eq) | 0 | 102 | 275 | 515 |
| PAS (sólo contexto) | 98 | 45 | 68 | 81 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,6 | 4,2 |

**meta del relleno (fracción de lo perdido) = 1.**

- bajo: 57m: cumple todas; 72f: cumple todas.
- medio: 57m: no cumple FD-BLD-07; 72f: no cumple FD-BLD-07.
- alto: 57m: no cumple U-OUT, FD-BLD-07; 72f: no cumple U-OUT, FD-BLD-07.

| 57m · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,148 |
| Hb (g/dL) | 6,70 | 6,69 | 6,64 | 6,47 |
| volumen circulante C (mL-eq) | 0 | -141 | -266 | -473 |
| precarga (posición) | 0,50 | 0,45 | 0,40 | 0,31 |
| gasto relativo | 1,00 | 0,90 | 0,81 | 0,63 |
| DO2 | 0,34 | 0,31 | 0,27 | 0,21 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,24 | 0,32 | 0,48 |
| relleno acumulado (mL-eq) | 0 | 9 | 34 | 127 |
| PAS (sólo contexto) | 88 | 84 | 79 | 71 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,7 | 3,4 |

| 57m · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,072 | -0,144 |
| Hb (g/dL) | 6,70 | 6,41 | 6,43 | 6,45 | 6,34 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -143 | -381 |
| precarga (posición) | 0,50 | 0,53 | 0,51 | 0,45 | 0,36 |
| gasto relativo | 1,00 | 1,05 | 1,01 | 0,90 | 0,71 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,29 | 0,23 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,14 | 0,18 | 0,26 | 0,43 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 25 | 120 |
| PAS (sólo contexto) | 88 | 90 | 88 | 83 | 75 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,3 |

| 57m · Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,074 | -0,074 | -0,074 |
| Hb (g/dL) | 6,70 | 6,64 | 6,54 | 6,40 |
| volumen circulante C (mL-eq) | 0 | -261 | -203 | -123 |
| precarga (posición) | 0,50 | 0,40 | 0,43 | 0,46 |
| gasto relativo | 1,00 | 0,81 | 0,85 | 0,91 |
| DO2 | 0,34 | 0,27 | 0,28 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,32 | 0,29 | 0,26 |
| relleno acumulado (mL-eq) | 0 | 34 | 92 | 172 |
| PAS (sólo contexto) | 88 | 79 | 81 | 84 |
| lactato (sólo contexto) | 4,4 | 3,7 | 3,3 | 2,9 |

| 72f · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,148 |
| Hb (g/dL) | 6,40 | 6,39 | 6,34 | 6,18 |
| volumen circulante C (mL-eq) | 0 | -141 | -266 | -473 |
| precarga (posición) | 0,60 | 0,56 | 0,52 | 0,45 |
| gasto relativo | 1,00 | 0,93 | 0,87 | 0,75 |
| DO2 | 0,34 | 0,32 | 0,29 | 0,25 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,21 | 0,27 | 0,38 |
| relleno acumulado (mL-eq) | 0 | 9 | 34 | 127 |
| PAS (sólo contexto) | 98 | 95 | 92 | 87 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 2,9 |

| 72f · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,072 | -0,144 |
| Hb (g/dL) | 6,40 | 6,12 | 6,14 | 6,16 | 6,05 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -143 | -381 |
| precarga (posición) | 0,60 | 0,62 | 0,60 | 0,56 | 0,48 |
| gasto relativo | 1,00 | 1,04 | 1,01 | 0,93 | 0,81 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,31 | 0,26 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,16 | 0,18 | 0,24 | 0,35 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 25 | 120 |
| PAS (sólo contexto) | 98 | 100 | 98 | 95 | 89 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,9 |

| 72f · Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,074 | -0,074 | -0,074 |
| Hb (g/dL) | 6,40 | 6,34 | 6,25 | 6,12 |
| volumen circulante C (mL-eq) | 0 | -261 | -203 | -123 |
| precarga (posición) | 0,60 | 0,52 | 0,54 | 0,57 |
| gasto relativo | 1,00 | 0,87 | 0,90 | 0,94 |
| DO2 | 0,34 | 0,29 | 0,30 | 0,31 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,26 | 0,25 | 0,23 |
| relleno acumulado (mL-eq) | 0 | 34 | 92 | 172 |
| PAS (sólo contexto) | 98 | 92 | 94 | 95 |
| lactato (sólo contexto) | 3,4 | 3,1 | 2,9 | 2,6 |

**τ del relleno (min) = 480.**

- bajo: 57m: no cumple U-OUT, FD-BLD-07; 72f: no cumple U-OUT, FD-BLD-07.
- medio: 57m: no cumple FD-BLD-07; 72f: no cumple FD-BLD-07.
- alto: 57m: no cumple FD-BLD-07; 72f: no cumple FD-BLD-07.

| 57m · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,149 |
| Hb (g/dL) | 6,70 | 6,69 | 6,68 | 6,61 |
| volumen circulante C (mL-eq) | 0 | -147 | -287 | -549 |
| precarga (posición) | 0,50 | 0,45 | 0,39 | 0,28 |
| gasto relativo | 1,00 | 0,90 | 0,79 | 0,56 |
| DO2 | 0,34 | 0,30 | 0,27 | 0,19 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,24 | 0,33 | 0,53 |
| relleno acumulado (mL-eq) | 0 | 3 | 13 | 51 |
| PAS (sólo contexto) | 88 | 83 | 79 | 68 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,7 | 3,4 |

| 57m · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,073 | -0,145 |
| Hb (g/dL) | 6,70 | 6,41 | 6,43 | 6,47 | 6,46 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -159 | -453 |
| precarga (posición) | 0,50 | 0,53 | 0,51 | 0,44 | 0,32 |
| gasto relativo | 1,00 | 1,05 | 1,01 | 0,89 | 0,65 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,29 | 0,21 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,14 | 0,18 | 0,27 | 0,47 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 9 | 48 |
| PAS (sólo contexto) | 88 | 90 | 88 | 83 | 72 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,3 |

| 57m · Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,074 | -0,074 | -0,074 |
| Hb (g/dL) | 6,70 | 6,68 | 6,63 | 6,56 |
| volumen circulante C (mL-eq) | 0 | -282 | -257 | -217 |
| precarga (posición) | 0,50 | 0,40 | 0,41 | 0,42 |
| gasto relativo | 1,00 | 0,79 | 0,81 | 0,84 |
| DO2 | 0,34 | 0,27 | 0,27 | 0,28 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,33 | 0,32 | 0,30 |
| relleno acumulado (mL-eq) | 0 | 13 | 38 | 78 |
| PAS (sólo contexto) | 88 | 79 | 80 | 81 |
| lactato (sólo contexto) | 4,4 | 3,7 | 3,4 | 3,0 |

| 72f · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,149 |
| Hb (g/dL) | 6,40 | 6,39 | 6,38 | 6,31 |
| volumen circulante C (mL-eq) | 0 | -147 | -287 | -549 |
| precarga (posición) | 0,60 | 0,56 | 0,52 | 0,42 |
| gasto relativo | 1,00 | 0,93 | 0,86 | 0,71 |
| DO2 | 0,34 | 0,32 | 0,29 | 0,24 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,21 | 0,27 | 0,41 |
| relleno acumulado (mL-eq) | 0 | 3 | 13 | 51 |
| PAS (sólo contexto) | 98 | 95 | 92 | 85 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 3,0 |

| 72f · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,073 | -0,145 |
| Hb (g/dL) | 6,40 | 6,12 | 6,14 | 6,18 | 6,17 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -159 | -453 |
| precarga (posición) | 0,60 | 0,62 | 0,60 | 0,56 | 0,46 |
| gasto relativo | 1,00 | 1,04 | 1,01 | 0,93 | 0,77 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,30 | 0,25 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,16 | 0,18 | 0,24 | 0,37 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 9 | 48 |
| PAS (sólo contexto) | 98 | 100 | 98 | 95 | 87 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,9 |

| 72f · Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,074 | -0,074 | -0,074 |
| Hb (g/dL) | 6,40 | 6,38 | 6,34 | 6,27 |
| volumen circulante C (mL-eq) | 0 | -282 | -257 | -217 |
| precarga (posición) | 0,60 | 0,52 | 0,53 | 0,54 |
| gasto relativo | 1,00 | 0,86 | 0,88 | 0,90 |
| DO2 | 0,34 | 0,29 | 0,29 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,27 | 0,26 | 0,25 |
| relleno acumulado (mL-eq) | 0 | 13 | 38 | 78 |
| PAS (sólo contexto) | 98 | 92 | 92 | 93 |
| lactato (sólo contexto) | 3,4 | 3,1 | 2,9 | 2,7 |

**τ del relleno (min) = 960.**

- bajo: 57m: no cumple U-OUT, FD-BLD-07; 72f: no cumple U-OUT, FD-BLD-07.
- medio: 57m: no cumple FD-BLD-07; 72f: no cumple FD-BLD-07.
- alto: 57m: no cumple FD-BLD-07; 72f: no cumple FD-BLD-07.

| 57m · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,150 |
| Hb (g/dL) | 6,70 | 6,70 | 6,69 | 6,65 |
| volumen circulante C (mL-eq) | 0 | -148 | -293 | -573 |
| precarga (posición) | 0,50 | 0,45 | 0,39 | 0,27 |
| gasto relativo | 1,00 | 0,90 | 0,78 | 0,53 |
| DO2 | 0,34 | 0,30 | 0,27 | 0,18 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,24 | 0,33 | 0,55 |
| relleno acumulado (mL-eq) | 0 | 2 | 7 | 27 |
| PAS (sólo contexto) | 88 | 83 | 78 | 67 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,7 | 3,4 |

| 57m · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,073 | -0,145 |
| Hb (g/dL) | 6,70 | 6,41 | 6,43 | 6,48 | 6,50 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -163 | -476 |
| precarga (posición) | 0,50 | 0,53 | 0,51 | 0,44 | 0,31 |
| gasto relativo | 1,00 | 1,05 | 1,01 | 0,89 | 0,63 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,29 | 0,21 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,14 | 0,18 | 0,27 | 0,48 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 5 | 25 |
| PAS (sólo contexto) | 88 | 90 | 88 | 83 | 71 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,3 |

| 57m · Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,074 | -0,074 | -0,074 |
| Hb (g/dL) | 6,70 | 6,69 | 6,66 | 6,62 |
| volumen circulante C (mL-eq) | 0 | -288 | -275 | -252 |
| precarga (posición) | 0,50 | 0,39 | 0,40 | 0,41 |
| gasto relativo | 1,00 | 0,79 | 0,80 | 0,82 |
| DO2 | 0,34 | 0,27 | 0,27 | 0,27 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,33 | 0,32 | 0,31 |
| relleno acumulado (mL-eq) | 0 | 7 | 20 | 43 |
| PAS (sólo contexto) | 88 | 78 | 79 | 80 |
| lactato (sólo contexto) | 4,4 | 3,7 | 3,4 | 3,1 |

| 72f · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,150 |
| Hb (g/dL) | 6,40 | 6,40 | 6,39 | 6,35 |
| volumen circulante C (mL-eq) | 0 | -148 | -293 | -573 |
| precarga (posición) | 0,60 | 0,56 | 0,51 | 0,41 |
| gasto relativo | 1,00 | 0,93 | 0,86 | 0,69 |
| DO2 | 0,34 | 0,32 | 0,29 | 0,23 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,21 | 0,27 | 0,42 |
| relleno acumulado (mL-eq) | 0 | 2 | 7 | 27 |
| PAS (sólo contexto) | 98 | 95 | 92 | 84 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 3,0 |

| 72f · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,073 | -0,145 |
| Hb (g/dL) | 6,40 | 6,12 | 6,14 | 6,19 | 6,21 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -163 | -476 |
| precarga (posición) | 0,60 | 0,62 | 0,60 | 0,55 | 0,45 |
| gasto relativo | 1,00 | 1,04 | 1,01 | 0,92 | 0,75 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,30 | 0,25 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,16 | 0,18 | 0,24 | 0,38 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 5 | 25 |
| PAS (sólo contexto) | 98 | 100 | 98 | 95 | 87 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,9 |

| 72f · Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,074 | -0,074 | -0,074 |
| Hb (g/dL) | 6,40 | 6,39 | 6,37 | 6,33 |
| volumen circulante C (mL-eq) | 0 | -288 | -275 | -252 |
| precarga (posición) | 0,60 | 0,52 | 0,52 | 0,53 |
| gasto relativo | 1,00 | 0,86 | 0,87 | 0,88 |
| DO2 | 0,34 | 0,29 | 0,29 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,27 | 0,27 | 0,26 |
| relleno acumulado (mL-eq) | 0 | 7 | 20 | 43 |
| PAS (sólo contexto) | 98 | 92 | 92 | 93 |
| lactato (sólo contexto) | 3,4 | 3,1 | 2,9 | 2,7 |

**posición de precarga de llegada (57m) = 0,65.**

- bajo: 57m: no cumple U-OUT; 72f: cumple todas.
- medio: 57m: no cumple U-OUT; 72f: cumple todas.
- alto: 57m: no cumple U-OUT; 72f: cumple todas.

| 57m · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,149 |
| Hb (g/dL) | 6,70 | 6,69 | 6,66 | 6,53 |
| volumen circulante C (mL-eq) | 0 | -143 | -274 | -505 |
| precarga (posición) | 0,65 | 0,61 | 0,58 | 0,51 |
| gasto relativo | 1,00 | 0,95 | 0,89 | 0,78 |
| DO2 | 0,34 | 0,32 | 0,30 | 0,26 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,20 | 0,25 | 0,35 |
| relleno acumulado (mL-eq) | 0 | 7 | 26 | 95 |
| PAS (sólo contexto) | 88 | 86 | 83 | 78 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,7 | 3,3 |

| 57m · GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | 0,246 | 0,493 |
| Hb (g/dL) | 6,70 | 7,77 | 8,70 |
| volumen circulante C (mL-eq) | 0 | 300 | 600 |
| precarga (posición) | 0,65 | 0,71 | 0,77 |
| gasto relativo | 1,00 | 1,10 | 1,18 |
| DO2 | 0,34 | 0,43 | 0,52 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| PAS (sólo contexto) | 88 | 92 | 96 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,6 |

| 57m · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,073 | -0,145 |
| Hb (g/dL) | 6,70 | 6,41 | 6,43 | 6,46 | 6,39 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -150 | -411 |
| precarga (posición) | 0,65 | 0,67 | 0,65 | 0,61 | 0,54 |
| gasto relativo | 1,00 | 1,03 | 1,01 | 0,94 | 0,83 |
| DO2 | 0,34 | 0,33 | 0,33 | 0,31 | 0,27 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,16 | 0,18 | 0,23 | 0,33 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 18 | 90 |
| PAS (sólo contexto) | 88 | 89 | 88 | 85 | 80 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,2 |

**posición de precarga de llegada (57m) = 0,8.**

- bajo: 57m: no cumple U-OUT; 72f: cumple todas.
- medio: 57m: no cumple U-OUT; 72f: cumple todas.
- alto: 57m: no cumple U-OUT; 72f: cumple todas.

| 57m · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,149 |
| Hb (g/dL) | 6,70 | 6,69 | 6,66 | 6,53 |
| volumen circulante C (mL-eq) | 0 | -143 | -274 | -505 |
| precarga (posición) | 0,80 | 0,78 | 0,76 | 0,72 |
| gasto relativo | 1,00 | 0,97 | 0,95 | 0,90 |
| DO2 | 0,34 | 0,33 | 0,32 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,17 | 0,20 | 0,25 |
| relleno acumulado (mL-eq) | 0 | 7 | 26 | 95 |
| PAS (sólo contexto) | 88 | 87 | 86 | 83 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,7 | 3,2 |

| 57m · GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | 0,246 | 0,493 |
| Hb (g/dL) | 6,70 | 7,77 | 8,70 |
| volumen circulante C (mL-eq) | 0 | 300 | 600 |
| precarga (posición) | 0,80 | 0,84 | 0,87 |
| gasto relativo | 1,00 | 1,05 | 1,08 |
| DO2 | 0,34 | 0,41 | 0,48 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| PAS (sólo contexto) | 88 | 90 | 92 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,6 |

| 57m · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,073 | -0,145 |
| Hb (g/dL) | 6,70 | 6,41 | 6,43 | 6,46 | 6,39 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -150 | -411 |
| precarga (posición) | 0,80 | 0,81 | 0,80 | 0,78 | 0,74 |
| gasto relativo | 1,00 | 1,01 | 1,00 | 0,97 | 0,92 |
| DO2 | 0,34 | 0,33 | 0,33 | 0,32 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,18 | 0,18 | 0,20 | 0,25 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 18 | 90 |
| PAS (sólo contexto) | 88 | 89 | 88 | 87 | 84 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,2 |

**posición de precarga de llegada (72f) = 0,75.**

- bajo: 57m: cumple todas; 72f: no cumple U-OUT.
- medio: 57m: cumple todas; 72f: no cumple U-OUT.
- alto: 57m: cumple todas; 72f: no cumple U-OUT.

| 72f · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,149 |
| Hb (g/dL) | 6,40 | 6,39 | 6,36 | 6,24 |
| volumen circulante C (mL-eq) | 0 | -143 | -274 | -505 |
| precarga (posición) | 0,75 | 0,72 | 0,70 | 0,65 |
| gasto relativo | 1,00 | 0,97 | 0,93 | 0,87 |
| DO2 | 0,34 | 0,33 | 0,32 | 0,29 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,18 | 0,21 | 0,28 |
| relleno acumulado (mL-eq) | 0 | 7 | 26 | 95 |
| PAS (sólo contexto) | 98 | 96 | 95 | 92 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 2,8 |

| 72f · GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | 0,258 | 0,516 |
| Hb (g/dL) | 6,40 | 7,49 | 8,43 |
| volumen circulante C (mL-eq) | 0 | 300 | 600 |
| precarga (posición) | 0,75 | 0,80 | 0,83 |
| gasto relativo | 1,00 | 1,06 | 1,11 |
| DO2 | 0,34 | 0,42 | 0,50 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| PAS (sólo contexto) | 98 | 101 | 103 |
| lactato (sólo contexto) | 3,4 | 3,2 | 3,0 |

| 72f · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,073 | -0,145 |
| Hb (g/dL) | 6,40 | 6,12 | 6,14 | 6,17 | 6,10 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -150 | -411 |
| precarga (posición) | 0,75 | 0,76 | 0,75 | 0,72 | 0,67 |
| gasto relativo | 1,00 | 1,02 | 1,00 | 0,97 | 0,89 |
| DO2 | 0,34 | 0,33 | 0,33 | 0,32 | 0,29 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,17 | 0,18 | 0,21 | 0,27 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 18 | 90 |
| PAS (sólo contexto) | 98 | 99 | 98 | 96 | 93 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,8 |

**posición de precarga de llegada (72f) = 0,9.**

- bajo: 57m: cumple todas; 72f: no cumple U-OUT.
- medio: 57m: cumple todas; 72f: no cumple U-OUT.
- alto: 57m: cumple todas; 72f: no cumple U-OUT.

| 72f · Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,149 |
| Hb (g/dL) | 6,40 | 6,39 | 6,36 | 6,24 |
| volumen circulante C (mL-eq) | 0 | -143 | -274 | -505 |
| precarga (posición) | 0,90 | 0,89 | 0,88 | 0,86 |
| gasto relativo | 1,00 | 0,99 | 0,98 | 0,96 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,32 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,16 | 0,17 | 0,21 |
| relleno acumulado (mL-eq) | 0 | 7 | 26 | 95 |
| PAS (sólo contexto) | 98 | 97 | 97 | 96 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 2,8 |

| 72f · GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | 0,258 | 0,516 |
| Hb (g/dL) | 6,40 | 7,49 | 8,43 |
| volumen circulante C (mL-eq) | 0 | 300 | 600 |
| precarga (posición) | 0,90 | 0,92 | 0,93 |
| gasto relativo | 1,00 | 1,02 | 1,04 |
| DO2 | 0,34 | 0,41 | 0,46 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| PAS (sólo contexto) | 98 | 99 | 100 |
| lactato (sólo contexto) | 3,4 | 3,2 | 3,0 |

| 72f · 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,073 | -0,145 |
| Hb (g/dL) | 6,40 | 6,12 | 6,14 | 6,17 | 6,10 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -150 | -411 |
| precarga (posición) | 0,90 | 0,91 | 0,90 | 0,89 | 0,87 |
| gasto relativo | 1,00 | 1,01 | 1,00 | 0,99 | 0,96 |
| DO2 | 0,34 | 0,33 | 0,33 | 0,32 | 0,31 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,18 | 0,18 | 0,19 | 0,22 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 18 | 90 |
| PAS (sólo contexto) | 98 | 98 | 98 | 97 | 96 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,8 |

### Filas ilegibles

| Caso y tabla | Filas |
|---|---|
| gi_bleed_57m|crystalloid | 3294 |
| gi_bleed_57m|stopped | 78 |
| gi_bleed_57m|untreated_blood | 162 |
| gi_bleed_72f|crystalloid | 1890 |
| gi_bleed_72f|untreated_blood | 90 |

Mensajes (hasta 20): `AssertionError: gi_bleed_57m/stopped_bleed: the blood reading's haemodynamics stopped at 53`; `AssertionError: gi_bleed_57m/stopped_bleed: the blood reading's haemodynamics stopped at 54`; `AssertionError: gi_bleed_57m/stopped_bleed: the blood reading's haemodynamics stopped at 55`; `AssertionError: gi_bleed_57m/stopped_bleed: the blood reading's haemodynamics stopped at 56`; `AssertionError: gi_bleed_57m/stopped_bleed: the blood reading's haemodynamics stopped at 57`; `AssertionError: gi_bleed_57m/stopped_bleed: the blood reading's haemodynamics stopped at 58`; `AssertionError: gi_bleed_57m/stopped_bleed: the blood reading's haemodynamics stopped at 59`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 105`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 106`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 107`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 108`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 109`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 110`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 112`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 113`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 114`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 116`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 117`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 119`; `AssertionError: gi_bleed_57m/untreated: the blood reading's haemodynamics stopped at 121`

<!-- /generado:extension -->

### 3.1 Lectura por dimensión

Todo vale a la resolución del diseño: dos pasos por dimensión, sin densificar entre ellos.

**Tasa de sangrado común (P2I-2W-5): acotada por U-OUT dentro del diseño; borde INTERIOR (2,5–5) sólo dentro del
diseño.**
- Con 10 y con 20 mL-eq/min ningún candidato conjunto sobrevive ni queda ilegible, en ninguna caja: ni sola, ni con la
  meta en 1,0, ni con τ 480 o 960, ni con las posiciones extendidas, ni en la esquina.
- Lo rechaza U-OUT, que falla en todos los candidatos de esas cajas. En la caja de cada tasa sola, todas las filas sin
  tratar quedan bajo su envolvente a los 30, 60 y 120 min: a los 120 min, 0,00–0,21 en 57m (mínimo 0,45) y 0,00–0,47
  en 72f (mínimo 0,60). Con 20, el ventrículo se vacía en todas esas filas.
- La Hb pesa poco donde se puede leer: U-HB falla en algunos candidatos con 10 (en la caja sola, por una sola fila de
  72f a los 120 min), pero nunca es la única restricción que los rechaza.
- En la caja de 10 sola, la lectura sanguínea congelada no se puede leer en 21 de las 36 filas de Hb de 57m. En la de
  20 sola, en ninguna fila de Hb de ningún caso. U-OUT ya rechaza esos candidatos conjuntos.
- El relleno no compensa: ni la meta en 1,0 ni una τ más lenta rescatan una tasa de 10.
- Dentro del diseño, la tasa queda acotada ya en el primer paso. Entre 5 y 10 el diseño no dice dónde está el límite.
- **Fuera del diseño no está demostrado.**
  - Con 10, 57m solo deja de ser rechazado únicamente al llegar en 0,65, y ahí queda ilegible (1944 candidatos).
  - 72f sola sobrevive con 10 al llegar en 0,75 (2394).
  - La terna «tasa 10, 57m en 0,65 y 72f en 0,75» no está en el diseño congelado, que sólo tiene pares y la esquina, y
    no se evaluó. Por la política congelada, lo ilegible no cuenta como cota.
- **Sensibilidad por caso.**
  - 72f sola tolera 10 únicamente si llega en 0,75 o 0,9 (2394 candidatos con cada una), es decir, en la banda
    euvolémica de referencia o por encima.
  - 57m solo nunca sobrevive con 10: queda rechazado, salvo con 0,65, donde queda ilegible.
  - Con 20 ningún caso sobrevive solo; 72f en 0,9 queda ilegible (1836).
- No se puebla ningún valor de familia: la política de producción sigue en CASE_OVERRIDES_FAMILY_DEFAULT.

**Posición de llegada (P2I-2W-4): acotada por arriba por U-OUT, y con una interacción fuerte; borde INTERIOR.**
- 57m: sobreviven 0,5 y 0,65; 0,8 no sobrevive en ninguna caja, ni siquiera con 57m solo. 72f: sobreviven 0,6 y 0,75;
  0,9 no deja ningún sobreviviente conjunto; 72f sola sólo la tolera con la tasa en 10, y con 20 queda ilegible (la
  sensibilidad por caso de arriba).
- Lo rechaza U-OUT por arriba: con 0,8 y 0,9 el gasto sin tratar queda sobre su envolvente, porque el paciente se
  deteriora demasiado poco (57m a 0,8: 0,61–0,96 a los 120 min, máximo 0,65; 72f a 0,9: 0,83–0,98, máximo 0,78).
- 0,65 y 0,75 sobreviven sólo juntas: 2268 candidatos, todos con tasa 5 y λ/κ 833. Movidas de a una (la otra en 0,5 o
  0,6) no dejan ningún sobreviviente conjunto, aunque cada caso solo sí tiene los suyos.
- Clasificación pedida: A (acotada por las restricciones antes del segundo paso) y C (interacción fuerte entre las dos
  posiciones, la tasa y λ/κ). No B: el lado superior ya no queda abierto. No está identificada: sobreviven dos valores
  explorados en cada caso.
- Con una unidad, el gasto sube sólo 8–24 % en 57m a 0,65 y 5–15 % en 72f a 0,75; con 0,8 y 0,9, 4–11 % y 2–5 %. En
  los representativos movidos, el estado de extracción pasa de crítico a compensado con la primera unidad, como en la
  base.
- Los representativos de P2I-2V-R movidos a 0,65 o 0,75 no sobreviven: se mueven de a uno y ninguno tiene la combinación
  que sobrevive (tasa 5 con λ/κ 833).

**Meta del relleno (P2I-2W-6): sigue OPEN_UPPER_GRID_EDGE, en el límite del dominio.**
- 1,0 (todo lo perdido) sobrevive: 663 candidatos sola y 1512 con τ 480. El punto 1,25 se descartó antes de evaluar
  porque está fuera del dominio. La meta no se puede extender más.
- Sola, 1,0 sobrevive sólo con capacidad 100 y τ 120: la capacidad corta el relleno y la meta casi no pesa. Con τ 480
  sobrevive con capacidad 500 y 1000.
- FD-BLD-07 no se debilitó: sigue rechazando la mayoría de las filas con meta 1,0 (por arriba a los 60, 120 y 240 min).
- Las restricciones no ponen un techo propio a la meta. La meta, la τ y la capacidad se compensan entre sí: es una
  cresta, no un valor.

**τ del relleno (P2I-2W-6): acotada; borde INTERIOR (120–480), con 480 condicionada.**
- 960 no sobrevive en ninguna caja: FD-BLD-07 la rechaza por abajo a los 60, 120 y 240 min en todas sus filas (el
  relleno es demasiado lento).
- 480 sobrevive sólo con la meta en 1,0 (1512 candidatos): la τ lenta necesita la meta en su límite.
- La conducta tras la hemostasia (FD-BLD-08) no rechaza ningún candidato en estas cajas.

**Fracción retenida del cristaloide (P2I-2W-7): sin extender; sigue OPEN_UPPER_GRID_EDGE.**
- Sus valores explorados no tienen un paso constante (§2): la continuación es ambigua y no se eligió ningún valor. No
  se evaluaron FD-BLD-04, 05 ni 06 más allá de 0,3.
- Para cerrarla hace falta que la docencia elija la continuación (por ejemplo 0,4 y 0,5, o 0,45 y 0,675) u otra regla.

### 3.2 Bordes después de la extensión

- **Con borde interior dentro del diseño:**
  - la tasa común (2,5–5; fuera del diseño el lado de 10 no está demostrado, §3.1);
  - la τ del relleno (120–480; 480 sólo con la meta en 1,0);
  - la posición de cada caso (57m 0,5–0,65; 72f 0,6–0,75; los valores altos sólo juntos).
- **Siguen OPEN_UPPER_GRID_EDGE:** la meta del relleno (en el límite de su dominio) y la fracción retenida del
  cristaloide (continuación ambigua, sin extender).
- **OPEN_BOTH_GRID_EDGES, sin extender:** B0, λ/κ, la capacidad del relleno, la unidad de GR (contenido y volumen), la τ
  y la fracción transitoria del cristaloide, y ρ (que ninguna restricción lee). P2I-2V-R no las señaló abiertas y la
  docencia no autorizó extenderlas.
- La identificabilidad sigue siendo la regla congelada. Ningún parámetro queda WELL_CONSTRAINED: las posiciones, que
  antes lo eran sólo por estar en el borde, pasan a PARTIALLY_CONSTRAINED con borde interior.
- **Límite de la tabla de bordes.** La tabla cuenta como superviviente sólo lo que sobrevive. Un valor con todos sus
  candidatos ilegibles saldría INTERIOR, contra la política.
  - En esta corrida no ocurre: ningún candidato conjunto quedó ilegible, y una prueba lo exige.
  - Corregirlo cambia el código congelado, así que queda para un paquete posterior.

### 3.3 Contradicciones fisiológicas que deja la extensión

- **Posición de llegada euvolémica en un caso de hemorragia.** 57m a 0,65 y 72f a 0,75 caen dentro de la banda de
  referencia euvolémica (0,6–0,8) y fuera de la banda de llegada de cada caso, inferida del POCUS (57m 0,2–0,5 por la
  VCI colapsada y el VI casi obliterado; 72f 0,3–0,6).
  - Ahí la premisa de FD-BLD-02 («con llenado bajo») no se cumple.
  - El diagnóstico de FD-BLD-03 es degenerado: los 2268 sobrevivientes ya están en la referencia antes de la unidad.
  - Las restricciones docentes por sí solas no los excluyen; la banda de llegada del caso sí. Decidir si la banda del
    caso acota la posición es una decisión docente.
- **72f con tasa 10.** En la sensibilidad por caso, 72f solo tolera 10 mL-eq/min únicamente con la llegada en la banda
  euvolémica o por encima (0,75 o 0,9): la misma contradicción.
- **Meta del relleno en 1,0.** El plasma repondría todo lo perdido: sobrevive sólo cuando otra cosa la neutraliza (la
  capacidad de 100 mL-eq o una τ de 480). No es una contradicción con ninguna restricción, pero tampoco una cota.
- **La lectura sanguínea congelada falla con 10 y 20.**
  - `blood_constraints` lee la sangre con la posición superior y λ/κ 1500, con la premisa de que así ninguna superficie
    se detiene. Con 10 y 20 esa premisa no se cumple: el ventrículo de la lectura se vacía y quedan 5514 filas
    ilegibles, todas con esas tasas.
  - Es un límite del instrumento, no fisiología del candidato.
  - Ningún candidato conjunto queda ilegible: U-OUT los rechaza por el otro caso. Por caso sí quedan: 1944 de 57m
    (tasa 10, 0,65) y 1836 de 72f (tasa 20, 0,9).
- Las comprobaciones cruzadas de las tablas (Hb independiente de la hemodinámica; cristaloide retenido independiente del
  sangrado, B0 y relleno) no fallaron en ninguna fila extendida.

## 4. Auditoría semántica del nivel 1 y sondas históricas

<!-- generado:auditoria -->
| Comprobación | Escribe | Cómo | Clase | Por qué |
|---|---|---|---|---|
| RR1 (`check_rr1`) | V | V −8 por minuto durante 40 min y +900 en el minuto 40, desde la llegada sintética de las sondas | SYNTHETIC_STATE_PERTURBATION | un shock genérico y su corrección sobre la coordenada de precarga, para comprobar que aclarar el lactato no lleva la FR bajo su piso ventilatorio; sin caso GI, sin GR, sin relleno y sin cambio de Hb |
| HR1-HR4 (`check_hr`) | V | V −8 por minuto durante 30 min y +640 en el minuto 30, desde la llegada declarada de cada caso GI | SYNTHETIC_STATE_PERTURBATION | las reglas son la respuesta cronotrópica al deterioro y a la recuperación hemodinámicos (KD-S2, P2E-1, P2D-3) y leen sólo la FC y el impulso simpático. La pérdida mueve sólo V (sin GR, sin relleno, Hb sin cambio) y la reposición no es ningún producto: es una perturbación hipovolémica de la coordenada de precarga, no una hemorragia. Pasarla por BloodState exigiría valores de relleno y de volumen de llegada que no están aprobados |
| PL1-PL3 (`check_preload`) | V | V fijada en 0, 250, 500 y 750 en el minuto 0 de la llegada neutra (lecturas estáticas) | SYNTHETIC_STATE_PERTURBATION | lee la forma de la curva de precarga y el límite que pone una bomba deprimida; sin pérdida ni producto |
| PL4 (`check_congestion`) | V | V +2900 en el primer minuto, desde una llegada sintética con reserva de bomba 0,3 | SYNTHETIC_STATE_PERTURBATION | alcanzabilidad del agua pulmonar con exceso de precarga y reserva limitada: una carga de volumen, no un producto (la cinética del cristaloide no está aprobada) ni una hemorragia |
| DM1 (`check_demand`) | Hb | Hb −30 % en el minuto 0 de la llegada neutra | SYNTHETIC_STATE_PERTURBATION | una anemia aislada que fija la entrega mientras cambia la demanda; no hay pérdida de sangre |

Ninguna es PHYSIOLOGICAL_HAEMORRHAGE_PROBE, así que ninguna se convierte a BloodState. Todas siguen escribiendo la coordenada de forma directa, rotuladas, y no son evidencia sobre la fisiología de la hemorragia, la Hb ni la DO2 (`NOT_EVIDENCE_FOR` = haemorrhage, Hb, DO2).

| Sonda histórica de nivel 2 | Familia | Estado |
|---|---|---|
| `vasodilation_with_preload_loss` | sepsis | HISTORICAL_PROBE: fuera de `bands.PROBES`, de las bandas y de la tabla del arnés; no la lee ningún filtro |
| `pump_failure_then_bolus` | ACS | HISTORICAL_PROBE: fuera de `bands.PROBES`, de las bandas y de la tabla del arnés; no la lee ningún filtro |
| `preload_dependent` | RV infarct / PE | HISTORICAL_PROBE: fuera de `bands.PROBES`, de las bandas y de la tabla del arnés; no la lee ningún filtro |
| `overload` | pulmonary oedema | HISTORICAL_PROBE: fuera de `bands.PROBES`, de las bandas y de la tabla del arnés; no la lee ningún filtro |
<!-- /generado:auditoria -->

- **HR1–HR4.** El término «sangrado» era sólo el nombre de una variable (`bleed`) en `check_hr`. La regla congelada ya
  decía «pérdida de volumen». La corrida mueve sólo V: sin GR, sin relleno y sin cambio de Hb, y la «reposición» no es
  ningún producto. Es una perturbación hipovolémica sintética, no una hemorragia. La variable pasa a llamarse
  `volume_loss` y la regla no cambia.
- **Rótulo.** Las cinco quedan en `calibration.LEVEL1_DIRECT_WRITES` como SYNTHETIC_STATE_PERTURBATION. Una prueba exige
  que toda escritura directa de V o Hb de una comprobación activa esté registrada, que ninguna sea
  PHYSIOLOGICAL_HAEMORRHAGE_PROBE y que ninguna regla congelada use lenguaje de hemorragia.
- **Citas.** El motivo de rechazo de P2F en `decision_pack.py` decía «durante el sangrado» para la sonda HR1; ahora dice
  «durante la pérdida de volumen sintética de la sonda». El texto histórico del documento P2G (§11, opción
  `NO_REACHABILITY_RULE`) no se reescribe: su «durante el sangrado» se refiere a la misma sonda sintética, que P2G ya
  rotula como «sólo V».
- **Ninguna se convirtió a BloodState.** Convertir HR1–HR4 exigiría valores de relleno y de volumen de llegada no
  aprobados. Su clase A se apoya en lo que leen (FC e impulso simpático) y en que no mueven GR ni Hb; la confirma la
  docencia (§6).
- **Fuera del nivel 1.** Hay otras escrituras directas de V o Hb, rotuladas «bleed», en módulos de diagnóstico ya
  cerrados de P2I-2P, P2I-2Q y P2I-2S:
  - `haemorrhage_probes.py` (V y Hb a la vez);
  - `oxygen_probes.py` (Hb);
  - `hemodynamic_probes.py` (V).

  No son comprobaciones de nivel 1, no están en el arnés de calibración, ningún filtro las lee y sus documentos no se
  regeneran.
- **Sondas de bolo históricas (P2I-2W-9).** Siguen como HISTORICAL_PROBE, sin convertir. No forman parte de la evidencia
  de calibración activa y no influyen en ningún recuento: ni `blood_constraints` ni `blood_extension` las leen (una
  prueba lo exige).

## 5. Qué no hace

- No cambia ninguna restricción docente: `blood_constraints.py` es, byte a byte, el de P2I-2V-R (una prueba lo fija).
- No elige ningún conjunto final de parámetros ocultos: los sobrevivientes extendidos no son una aprobación.
- No refiltra el lactato, no usa lactato, PAS ni PAM para filtrar, no calibra la presión ni la FC y no activa el colapso.
- No extiende dimensiones no señaladas ni hace un barrido cartesiano completo.
- No migra, no integra y no puebla ningún valor de familia.

## 6. Decisiones pendientes (docencia)

- **La terna «tasa 10, 57m 0,65 y 72f 0,75».** No está en el diseño y ahí 57m queda ilegible. Para cerrar el lado de
  10 hace falta autorizar un congelamiento nuevo que la evalúe.
- **La lectura sanguínea congelada falla con 10 y 20.** Decidir cómo leer la sangre donde se detiene, por ejemplo con
  la propia hemodinámica del candidato.
- **La tabla de bordes trata lo ilegible como no superviviente.** Corregirla en un paquete posterior, con congelamiento
  nuevo.
- **HR1–HR4 como SYNTHETIC_STATE_PERTURBATION.** Confirmar la clase, y el uso de la sonda HR1 en `p2f_rejection`
  (`decision_pack.py`). Esa sonda excluye la posición 0,2 de 57m en la región admisible de P2F, P2G y P2I-1, y P2G §11
  la compara con la tasa del caso.
- La continuación de la fracción retenida del cristaloide (ambigua), para poder cerrar P2I-2W-7.
- Si la banda de llegada de cada caso (POCUS) acota la posición, lo que excluiría 0,65 / 0,75.
- Si la meta del relleno en 1,0 es aceptable o necesita un techo propio.
- Si las dimensiones OPEN_BOTH_GRID_EDGES (B0, λ/κ, capacidad, unidad de GR, cinética del cristaloide) deben
  extenderse en un paquete posterior.
- Si se densifica entre 5 y 10 mL-eq/min y entre 0,5–0,65 / 0,6–0,75, para ubicar el límite con más resolución.
