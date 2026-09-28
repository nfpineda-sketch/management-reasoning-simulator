# VALIDATION PILOT BASELINE

La versión del motor contra la que se leerán **primero** los documentos de los
médicos (§56, §57).

| Campo | Valor |
|---|---|
| **PILOT BASELINE COMMIT** | `bf21072f4109912db7f77eb7c8f90ab35b9df351` |
| Rama | `clinical-encounter-v0.13` |
| **ENGINE VERSION** | `0.24.13-clinical-encounter` (`SIMULATOR_VERSION` de `app.py`) |
| Plantilla / anotación | `VC2` / `VC2-ANNOTATION-1` |
| **DATE** | 2026-09-28 |
| Defectos conocidos | 14 (KD-01 a KD-14) y 1 conducta por diseño (KB-01): `KNOWN_DEFECTS.md` |

## Qué contiene

- **DF-16a y DF-16b**, corregidos por clase en inglés y español:
  - las listas de órdenes conservan cada orden;
  - una repetición deja correr su orden y queda como plan con su intervalo,
    número y condición;
  - la vía compartida por una lista de dosis.
- **La herramienta del validation corpus** en la versión del paquete:
  - plantilla VC2;
  - sorteo;
  - doble anotación;
  - taxonomía del §40;
  - el plan con su tipo, corregido.
- **Los 18 documentos** del piloto y las 12 plantillas en blanco.

## Pruebas registradas en este commit (§72)

| Requisito | Resultado |
|---|---|
| Pruebas de DF-16 | `test_lists_and_repeats_keep_every_order.py`: 60 pasan |
| Lectura de órdenes y fidelidad del razonamiento | los 69 archivos que usan el lector o la traza: 1788 pasan y 2 xfail (con las 50 primeras pruebas de DF-16) |
| Herramienta del validation corpus y paquete del piloto | `test_validation_corpus.py` 33, `test_pilot_package.py` 28, `test_c14_review.py` 8, `test_tools_order_reading.py` 5: todas pasan |
| Regresiones | 56 de 56 |
| Corpus de ensayo (20 guiones ES + 20 EN, semilla 3000) | 96/96 órdenes en cada idioma, 0 retenciones no previstas; idéntico al ciclo 3 decisión por decisión |
| Suite completa (4 shards) | corriendo al hacer este commit; el resultado se registra en el commit siguiente |

## Cómo se usa

- **Correr el motor sobre los documentos en este commit.** Use
  `git checkout bf21072f…`, o compruebe que
  `git diff bf21072f4109912db7f77eb7c8f90ab35b9df351 -- '*.py'` salga vacío.
  `engine_output.json` registra el commit y si había cambios sin guardar.
- **Usar este commit en el sorteo** (`SPLIT_PROCEDURE.md`, `--baseline`).
- **No se corrige el lector** por defectos hipotéticos o LOW después de este
  commit (§56).
- **Las respuestas de los médicos se miden primero contra este baseline**,
  antes de usarlas para cambiar el motor (§57). Nunca se modifica el baseline
  para que una respuesta pase.
- **Los commits posteriores del ciclo 4 son sólo de documentación.**
