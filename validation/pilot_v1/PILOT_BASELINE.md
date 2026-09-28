# VALIDATION PILOT BASELINE

La versión del motor contra la que se leerán **primero** los documentos de los
médicos (§56, §57).

| Campo | Valor |
|---|---|
| **PILOT BASELINE COMMIT** | `939978a5147ab859a6dc3566ef4e1a98611a5093` |
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
| Herramienta del validation corpus y paquete del piloto | `test_validation_corpus.py` 33, `test_pilot_package.py` 28, `test_c14_review.py` 9, `test_tools_order_reading.py` 4: todas pasan |
| Regresiones | 56 de 56, en las dos corridas completas |
| Corpus de ensayo (20 guiones ES + 20 EN, semilla 3000) | 96/96 órdenes en cada idioma, 0 retenciones no previstas; idéntico al ciclo 3 decisión por decisión |
| Suite completa (4 shards), en este commit | **4877 pasan, 77 omitidas, 2 xfail, 0 fallas** |

**Por qué el baseline es `939978a` y no `bf21072`.**

- **La primera corrida completa**, sobre `bf21072`, dio 5 fallas dependientes
  del orden en un shard: un escenario de órdenes mixtas y cuatro pruebas del
  banco de imágenes. Aisladas pasaban.
- **Causa, reproducida.** La prueba nueva de DF-16 por la página real fijaba
  `MRS_OFFLINE_CASES` en `os.environ`, y los archivos siguientes del mismo
  proceso la heredaban. La prueba del validation corpus tenía la misma fuga
  latente.
- **Corrección, en `939978a`.** Las dos pruebas usan ahora `monkeypatch`.
- **El código de la aplicación es idéntico** en los dos commits: sólo
  cambiaron esas dos pruebas.
- **La segunda corrida**, sobre este commit, no tuvo fallas.

## Cómo se usa

- **Correr el motor sobre los documentos en este commit.** Use
  `git checkout 939978a5147a`, o compruebe que
  `git diff 939978a5147ab859a6dc3566ef4e1a98611a5093 -- '*.py'` salga vacío.
  `engine_output.json` registra el commit y si había cambios sin guardar.
- **Usar este commit en el sorteo** (`SPLIT_PROCEDURE.md`, `--baseline`).
- **No se corrige el lector** por defectos hipotéticos o LOW después de este
  commit (§56).
- **Las respuestas de los médicos se miden primero contra este baseline**,
  antes de usarlas para cambiar el motor (§57). Nunca se modifica el baseline
  para que una respuesta pase.
- **Los commits posteriores del ciclo 4 son sólo de documentación.**

## Después del ciclo 5 (2026-09-28)

- **Este baseline no cambia.** Las respuestas en español se miden primero
  contra `939978a`.
- **El ENGLISH VALIDATION BASELINE es `ec1c77f`.** Trae KD-01 corregido y C14
  declarado (`validation/BASELINES.md`).
- **Un error de vía antes del fármaco leído aquí es KD-01**: en este baseline
  está presente.
