# Fase 3 · P3-20 · Auditoría técnica final antes de una autoridad limitada

Sólo lectura. Pregunta única: **¿lo que falta son decisiones docentes, o queda algo técnico?**

Rama `phase-3-runtime-integration`. El motor heredado sigue siendo la única autoridad en tiempo de
ejecución; `APPROVED_SNAPSHOTS` sigue vacío; el digesto de cierre de la Fase 2 `22b90a6f7f38…` recalcula
sobre las 141 fuentes y `clinical_core/` no tiene un byte distinto desde `d2cca46`.

## Inventario

| | Pieza | Estado | Evidencia |
|---|---|---|---|
| 1 | **Puerta** | `READY` | nueve condiciones; se **vuelve a evaluar en el commit**; la identidad del caso la decide el estado y no el llamador; una lista de acciones no declarada falla cerrado; una bandera nombrada en `secrets.toml` no se honra; el piloto está anclado a su propia congelación. `test_runtime_authority.py` A1–A17, C1–C12 |
| 2 | **Sitio de llamada** | `READY` | un solo punto de orquestación (`site_for`), el modo se decide una vez en el minuto 0, y en producción cuesta **0,13 µs por turno y cero digestos** (medido en la revisión adversarial). `test_runtime_authority_site.py` D1–D4, D16 |
| 3 | **Propiedad de la salida** | `READY` | `sbp` y `dbp` comunes; `map` escrito **como lo deriva la pantalla**, de modo que el estado, la pantalla y la traza de manejo coinciden; 16 variables heredadas y 4 sólo comparación; una escritura fuera de dominio la refuta el propio sitio. D7, D12, D20 |
| 4 | **Atomicidad** | `READY` | una escritura desde un único mapping preparado; el estado del llamador nunca se muta; cualquier fallo deja `ABORTED` y lanza `AuthorityRefused`; un minuto es una transacción y no se compromete dos veces. A7–A9, C6, C7, C9, D12, D23, G14 |
| 5 | **Elegibilidad** | `READY` | 34 escenarios: **26 válidos, 8 inelegibles**, y la lectura de elegibilidad y la de la transacción dan ahora **la misma** respuesta. G1–G4 |
| 6 | **Acción no soportada** | `READY` | falla cerrado ante las tres terapias sin escritor, ante una orden que el motor no modela, ante una sin tipo y ante una clase desconocida; las tres formas de clave del runtime (`type`, `kind`, `class`) se leen igual. G6, G16 |
| 7 | **Retroceso** | `READY` | el artefacto de retroceso se **materializa** al refutar, lleva los catorce campos que un lector necesita y reproduce el minuto fallido. G19, A10, D25 |
| 8 | **Procedencia** | `READY` | por minuto: encuentro, caso, familia, modo, instantánea y su procedencia, cabeza y digesto de la Fase 2, versión y digesto de capa, acciones con su suerte, digestos de entrada/candidato/replay/transacción, candidato común, lo escrito, contrafactual heredado, clases de divergencia, resultado y razón. D8, G17 |
| 9 | **Persistencia** | **`READY_WITH_LIMITATION`** | el artefacto existe, es completo, verificable y reproducible, y `authority_status()` es la lectura única que una superficie docente necesita. Lo que **no** existe: una superficie que lo muestre y un almacenamiento autorizado donde viva. La carga útil de producción es una lista blanca y dos de sus claves se copian tal cual, así que meter el registro ahí dentro está prohibido. Es el único paquete que queda | E10, G20, D24 |
| 10 | **Replay** | `READY` | cada minuto se reproduce desde el artefacto solo —tres minutos reales, tres digestos distintos, todo coincide—, un artefacto manipulado deja de reproducir, y el límite está dicho: el digesto detecta un cambio, no a un falsificador con la misma función de digesto | D14, D19, D25, G15 |
| 11 | **Camino de la aplicación** | `READY` | la app dibuja las presiones comprometidas, una transacción refutada deja las heredadas, el encuentro propio de la app **no** es un caso GI y no se le puede comprometer nada, y el bloque de `app.py` está fijado por AST a tres sentencias sin lógica propia | D3, D13–D18, E13, E14, E16 |
| 12 | **Exclusión del piloto** | `READY` | la condición se ancla a `pilot_freeze.RUNTIME_FLAGS` y falla cerrada si esa congelación no se puede leer; ninguna superficie del piloto nombra las banderas de autoridad | C10, E9, G11 |
| 13 | **Inmutabilidad de la Fase 2** | `READY` | el digesto recalcula; el invariante de aislamiento se reformuló a **la capa declarada** (dos cruces nombradas) con control negativo ejecutado: un módulo no declarado que lea la capa sigue haciendo fallar las pruebas | `test_shadow_core_isolation.py`, `test_phase2_closure.py` |

## Lo que queda

**Un paquete técnico, el de la fila 9**: la superficie docente del experimento —dónde se muestra un fallo
duro y dónde se guarda el artefacto— con la decisión docente que le corresponde (qué almacenamiento, cuánta
retención). Todo lo demás de este inventario está `READY`, y las demás ausencias son decisiones docentes,
no defectos: el punto de la instantánea, el criterio de aceptación, la lectura de las cuatro diferencias
parcialmente explicadas, si la falla cerrada ante las cuatro clases bloqueadas basta, y el consentimiento
del primer experimento.

Dos hechos que conviene no perder de vista, porque no son defectos y sí son consecuencias:

- **Con la bandera de autoridad puesta, cada minuto vuelve a correr la trayectoria completa del núcleo**
  para obtener el digesto de replay (coste cuadrático en la longitud del encuentro; ~3–25 ms por minuto en
  los encuentros medidos). Es el precio de que la reproducibilidad del minuto se compruebe de verdad y no
  se acepte del llamador. En producción no se paga nunca.
- **Un fallo duro después de un commit deja la trayectoria de presión mezclada** —heredada antes, común
  durante, heredada después—. No se puede deshacer retroactivamente, así que el artefacto lo **declara**
  (`mixed_trajectory`) y el rescate es leer el encuentro desde el artefacto, nunca continuarlo.

## Veredicto

**`ONE_TECHNICAL_PACKAGE_REMAINS`** — la superficie docente y el almacenamiento del artefacto del
experimento. No lo construyo: hacer que un fallo duro se muestre y que el artefacto se guarde toca la
pantalla y la persistencia, que esta autorización deja fuera, y además necesita la decisión docente de
dónde vive.
