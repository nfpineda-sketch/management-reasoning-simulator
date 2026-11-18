# Versionado de los registros históricos derivados de código (P3-388)

Fecha: 2026-11-17. Rama: `phase-3-runtime-integration`. Alcance: **contrato de registros** (`historical_records.py` y su índice);
no cambia fisiología, autoridad ni nada que vea el residente.
Decisiones: FD-RECORD-01 a FD-RECORD-04 y FD-P3-258 (`docs/COLA_DECISIONES_AI_ADVISOR.md`). Deuda: `TD-154`.

Distingo en todo el documento: **implementado** · **probado** · **pendiente**.

## 1 · El problema
Un registro de `docs/revision/` que un programa **generó** (un punto de control, una serie, un análisis, un conjunto candidato)
es evidencia de lo que una versión exacta del código produjo en una fecha. Dos veces en este proyecto un cambio posterior del
código hizo que una prueba del tipo «regenerar y comparar» dejara de coincidir con el registro guardado, y las únicas salidas
eran reescribir el registro —lo que destruye la evidencia— o abrir una excepción *ad hoc*. El ciclo de promoción del 2026-11-16
lo dejó anotado como pendiente («los registros históricos no se regeneraron»). Este contrato es la regla que sustituye a ambas
salidas.

## 2 · La regla (FD-RECORD-01 a FD-RECORD-04)
1. **Un registro histórico es inmutable.** Sus bytes quedan fijados en el índice
   `docs/revision/HISTORICAL_RECORD_INDEX.json`; un registro cuyos bytes cambiaron se rechaza por su nombre. Nunca se regenera
   bajo código nuevo, ni en silencio ni de otro modo.
2. **Un registro generado dice qué lo generó.** Lleva un bloque `provenance` con:

   | Campo | Qué es |
   |---|---|
   | `contract` | `P3-388_HISTORICAL_RECORD_VERSIONING` |
   | `record_schema_version` | versión del esquema del registro (entero ≥ 1) |
   | `record_id` | identificador versionado del registro |
   | `generating_code_fingerprint` | huella del código generador |
   | `generating_code` | las partes de las que sale esa huella (digesto del núcleo vivo y SHA-256 de cada archivo generador) |
   | `source_snapshot_id` | la instantánea de la que parte, si la hay |
   | `grant_id` | la concesión que lo ampara, si aplica |
   | `source_data_digest` | digesto de los datos de origen |
   | `generated_on` | fecha de generación (ISO, sin hora: ver §4) |
   | `supersedes` | el registro al que sucede y su SHA-256, o `null` |

   El registro completo queda **sellado** por `record_digest`, el digesto de todo lo demás.
3. **Una regeneración se compara con el registro guardado sólo bajo el mismo código generador** (`same_generating_code`). Bajo
   otro código, el registro guardado se verifica por lo que es —sellado, fijado, bien formado— y la salida del código nuevo es
   un registro **nuevo**.
4. **Una representación más nueva es un registro sucesor.** Nombra al que sucede y el digesto de ese archivo; el anterior queda
   donde está, byte por byte. Nada se edita en el sitio: `historical_records.write` se niega a reemplazar un archivo existente
   por otro contenido.

## 3 · Clases del índice
| Clase | Qué es | Qué garantiza el índice |
|---|---|---|
| `LEGACY_UNVERSIONED` | Registro anterior a este contrato. | Sus bytes (SHA-256), fijados desde los *blobs* del commit `caa0b0fd…` y **no** desde el árbol de trabajo. No lleva bloque de procedencia: no se le inventa uno. |
| `VERSIONED` | Registro generado bajo este contrato. | Bytes fijados, bloque de procedencia, sello e identificador. |
| `LINEAGE_RECORD_OPEN_UNTIL_CERTIFIED` | El registro propio de un sucesor del núcleo mientras su certificación está por escribirse. | Sólo su existencia: su bloque `certification` se escribe una vez, al certificar. |
| `LINEAGE_RECORD` | Ese mismo registro ya certificado. | Bytes fijados. Su formato es el de la compuerta de linaje, no el de este contrato. |

Los 101 registros anteriores quedan como `LEGACY_UNVERSIONED`; el digesto de ese conjunto de entradas queda fijado en el índice
y en la prueba (`legacy_entries_digest`), de modo que **quitar o cambiar una entrada heredada se detecta**.

## 4 · Decisiones de diseño
- **Fecha, no reloj.** Los registros del repositorio son funciones reproducibles de sus entradas; llevan una fecha que el
  generador declara como constante, no una marca de tiempo de pared. El encargo lo previó («si la convención lo permite»).
- **El módulo es puro** (`hashlib` y `json`): no lee el reloj, no importa nada del repositorio y no decide nada sobre el
  contenido de ningún registro.
- **A los registros heredados no se les agrega procedencia retroactiva.** Sería inventar un dato que no se registró cuando se
  generaron. Conservan lo único del contrato que pueden conservar: sus bytes.
- **Las pruebas «regenerar y comparar» que ya existían no se reescribieron en bloque.** Donde este ciclo las tocó (porque el
  núcleo vivo pasó a ser la Enmienda 3), la adaptación consistió en comparar lo que el registro dice de sí mismo y no en
  regenerarlo; cada una está declarada en `docs/PHASE3_COMMON_VASCULAR_TONE.md` §12.

## 5 · Implementado y probado
- **Implementado:** `historical_records.py` (`provenance`, `seal`, `record_problems`, `same_generating_code`, `write`,
  `index_problems`, `index_entry`, `legacy_digest`) y `docs/revision/HISTORICAL_RECORD_INDEX.json`.
- **Primeros registros `VERSIONED`:** `PHASE3_FRF_TONE_V1_CANDIDATE.json`, `PHASE3_COMMON_TONE_PROBES.json` y
  `PHASE3_COMMON_TONE_CHECKPOINT.json` (este ciclo).
- **Probado:** `test_phase3_historical_record_versioning.py` (contrato, sello, índice, sucesión, rechazo de reescritura,
  detección de un registro heredado cambiado o retirado) y `test_phase3_tone_pathway_records.py` (los registros nuevos bajo el
  contrato). Las cifras de la certificación están en `docs/PHASE3_COMMON_VASCULAR_TONE.md` §13.

## 6 · Pendiente
- Migrar a registros sucesores `VERSIONED` los registros heredados cuyo generador siga vivo, **sólo cuando haga falta una
  representación nueva** (no hay razón para hacerlo en bloque).
- Decidir si el índice debe cubrir también `faculty_review_kit/` y otros directorios con evidencia generada (`TD-154`).
