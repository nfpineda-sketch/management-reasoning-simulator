# P2X-1A · Reparación de las guardas del cierre de la Fase 2

Cambio común, en sombra. Rama `phase-2-clinical-core-shadow`; base `e0e520d` (P2X-1 aceptado, con su veredicto
operativo corregido por su propia revisión adversarial: **`PHASE2_DECLARED_PROPERTIES_NOT_CLOSED`**).

P2X-1 no es un paquete fallido: su derivación analítica, sus guardas y su contrato siguen en pie, y este paquete no
los reabre. Lo que su revisión demostró —y yo reproduje con mis propias sondas— fueron **dos bloqueos reales del
cierre** y un conjunto de criterios que no podían fallar. P2X-1A repara exactamente eso: guardas, falsabilidad y
trazabilidad. No añade fisiología clínica, no elige ninguna magnitud, no integra nada en tiempo de ejecución.

1. **La propiedad del canal T era condicional.** `step` llamaba a `_vascular_tone` sólo si la ganancia de
   compensación era mayor que 0 o el lector distributivo estaba declarado, y el rechazo de un segundo escritor de T
   vivía **dentro** de esa función. El perfil comprometido GI tiene las dos cosas apagadas: un escritor clínico de T
   llegaba al canal y su guarda —una cota de seguridad— fijaba el valor, con recortes registrados.
   `integration._tone_ownership` corre ahora en todo minuto de todo perfil, antes de reconstruir el canal.
2. **El dominio era inclusivo y el minuto aceptado podía llevar recorte.** La admisibilidad por minuto aceptaba un
   objetivo exactamente sobre la guarda de T, y la reconstrucción del canal dejaba un recorte de 2,8e-17 dentro de un
   minuto aceptado. El dominio soportado es ahora el intervalo **abierto**, y se comprueba el valor que el canal va a
   guardar de verdad, sin épsilon, margen ni tolerancia. La admisibilidad del objetivo mayor también es estricta, y
   ya no depende de que el lector esté declarado.
3. **Tres criterios no podían fallar y un resultado se calculaba sin leerse.** `contradictions`,
   `debt_classification` y `supersession` derivaban su veredicto de listas que construían vacías o de prosa no vacía,
   y la regla de disposición nunca leía la prueba de reversión. Los cuatro son ejecutables y falsables aquí.
4. **El escaneo del contrato del escritor era evadible.** Se le escapaban el constructor cualificado, la función
   auxiliar, el acceso posicional y los observables del mismo lazo fuera de su lista, y leía sólo los módulos del
   paquete. Ahora sigue alias, nombres cualificados y auxiliares del propio módulo, cubre todos los observables del
   lazo que el núcleo deriva, y lee el código del repositorio.

- **Cambio común mínimo** (`integration.py`, `provenance.py`; más las dos tuplas de registro), probado contra
  `e0e520d`:
  - `integration._tone_ownership`: la propiedad del canal T, incondicional, llamada desde `step`;
  - en `_vascular_tone`: frontera estricta por minuto sobre el objetivo **y** sobre la reconstrucción del canal, y
    admisibilidad estricta del objetivo mayor para todo perfil;
  - en `provenance.VasodilationChange`: el contrato publica lo que el escaneo reforzado exige.
- **Análisis:** `clinical_core/closure_guard.py`, congelado antes de la única evaluación. **Registro:**
  `docs/revision/P2X1A_closure_guard.json`. Este documento se genera desde el registro
  (`clinical_core/closure_guard_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Las decisiones docentes que rigen

<!-- generado:decisiones -->
<!-- /generado:decisiones -->

## 2. La interpretación declarada (y abierta a confirmación)

La decisión 1 dice «una familia o cualquier otra contribución». El repositorio ya clasifica a los escritores, y este
paquete usa esa clasificación en vez de inventar otra: rechaza toda fuente **clínica** en todo perfil, y deja a las
sondas sintéticas declaradas escribiendo T como ya escriben V y Hb. Lo que la revisión demostró —un módulo de
enfermedad aceptado en GI— queda cerrado. La lectura amplia retiraría tres sondas de banda y las lecturas cerradas que
las citan: eso es fisiología, y necesita otra autorización.

<!-- generado:interpretacion -->
<!-- /generado:interpretacion -->

## 3. Las guardas reparadas (P2X-1A-1, P2X-1A-2 y P2X-1A-3)

Lo que se añadió son **rechazos**, y uno de ellos cambió de sitio: la propiedad del canal salió de la respuesta y
pasó a `step`. Ninguna lectura aceptada cambia, el delta que el acoplamiento devuelve sigue siendo el mismo, y los
chequeos publicados de P2J-2 y de P2X-1 quedan intactos.

<!-- generado:guardas -->
<!-- /generado:guardas -->

## 4. El contrato del escritor, exigible (P2X-1A-8)

<!-- generado:contrato -->
<!-- /generado:contrato -->

## 5. Las veintidós sondas (A1–A22)

<!-- generado:sondas -->
<!-- /generado:sondas -->

## 6. Contradicciones, ahora decididas por sondas (P2X-1A-4)

<!-- generado:contradicciones -->
<!-- /generado:contradicciones -->

## 7. La deuda consolidada, trazada al registro (P2X-1A-5)

Ninguna entrada es bloqueo por estar UNSET: una magnitud UNSET deja su término inerte, que es el diseño. Lo que sí es
bloqueo es un bloqueo demostrado clasificado como deuda aceptable, y eso lo decide una sonda.

<!-- generado:deuda -->
<!-- /generado:deuda -->

## 8. Supersesiones, verificadas contra los artefactos (P2X-1A-6)

<!-- generado:supersesion -->
<!-- /generado:supersesion -->

## 9. No regresión y prueba de reversión (P2X-1A-7)

<!-- generado:no_regresion -->
<!-- /generado:no_regresion -->

## 10. Criterios y veredicto

<!-- generado:veredicto -->
<!-- /generado:veredicto -->

## 11. Qué NO hace este paquete

- No reabre la derivación de P2X-1: `B(b)`, `b ≥ 0`, la recuperación por debajo de la carga de llegada, `Bmax` y la
  cota de contracción derivada siguen como P2X-1 las dejó (decisión 4). No se encontró ningún error matemático.
- No implementa maldistribución, extracción, relleno capilar ni lactato distributivos, ni fuga de plasma, ni vía
  aérea alta, ni blancos de epinefrina (decisión 6).
- No abre presión → tono (decisión 5).
- No elige ninguna magnitud clínica, ni cota máxima de carga, ni parámetro de tono inferior, ni suelo de enfermedad,
  ni épsilon, ni factor de seguridad.
- No re-corta P2X-1, P2W-1, P2S-3 ni P2J-2: declara las supersesiones y verifica que sus digests no se movieron.
- No integra nada en tiempo de ejecución, no cambia lo que ve el residente y no inicia la Fase 3.
