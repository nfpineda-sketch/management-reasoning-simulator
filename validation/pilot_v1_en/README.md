# Piloto de validación en inglés · preparado, no enviado

Ciclo 7 · 2026-09-28 · §33–§37, §87 y §88 de la instrucción docente.

**Estado: PREPARED, NOT SENT.** Nadie fue contactado y no se distribuyó ningún
documento.

## Qué es

- **Un corpus separado.** El inglés no se mezcla con el español como si fuera
  un solo corpus. Tiene lo suyo:

  | | Español | Inglés |
  |---|---|---|
  | Corpus | `VALIDATION_CORPUS_V1` | `VALIDATION_CORPUS_V1_EN` |
  | Piloto | `VALIDATION_PILOT_V1` | `VALIDATION_PILOT_V1_EN` |
  | Participantes | EM01–EM06 | EM07–EM12 |
  | Asignación | `validation/pilot_v1/assignment_matrix.csv` | `assignment_matrix.csv` (aquí) |
  | Baseline | SPANISH PILOT BASELINE `939978a` | **por elegir** (abajo) |

- **Escritura natural en inglés.** Médicos que escriben en inglés, en texto
  libre. Nada se traduce desde respuestas en español.
- **Misma lógica que el español.** Los mismos seis casos, los mismos pares
  (EM07/EM08, EM09/EM10, EM11/EM12, con los mismos dos casos compartidos) y la
  misma regla de sorteo. `manifests/pilot_manifest.json` se generó desde el
  manifiesto español cambiando sólo los códigos y el idioma.

## Los documentos

**ENGLISH DOCX AVAILABLE EXTERNALLY / NOT PRESENT IN REPOSITORY.**

- No se regeneraron ni se inventó su contenido.
- **Antes de usarlos**, verificar cada uno contra su par español:
  - el mismo contenido del caso;
  - las mismas instrucciones;
  - la misma lógica de asignación;
  - distinto idioma de respuesta.
- Se pueden comparar byte a byte con lo que escribe
  `python3 tools_validation_corpus.py templates --pilot validation/pilot_v1_en/manifests/pilot_manifest.json --out DIR`.

## El baseline: se elige antes de leer

**Nunca el HEAD del ciclo elegido automáticamente, y nunca después de recibir o
leer las respuestas (§88).** Candidatos:

| Candidato | Commit | Estado |
|---|---|---|
| ENGLISH VALIDATION BASELINE | `ec1c77f` | Registrado en `validation/baselines.json` (ciclo 5) |
| DEVELOPMENT HARDENED BASELINE V1 | `72a4a53` | Referencia de desarrollo (ciclo 6), no de validación |
| DEVELOPMENT HARDENED BASELINE V2 | candidato del ciclo 7 | Referencia de desarrollo (ciclo 7), no de validación |

Ninguno se llama «validado».

## Cómo se procesa, con las mismas herramientas

1. **Guardar sin abrir** lo que vuelva.
2. **Sortear** con `tools_validation_corpus.py split --pilot
   validation/pilot_v1_en/manifests/pilot_manifest.json`. La regla es la de
   `validation/pilot_v1/SPLIT_PROCEDURE.md`.
3. **Anotar a ciegas, correr el baseline elegido y medir**, como en español.
   El subconjunto sellado no se usa.

## La guardia de idioma

`validation_corpus.corpus_language` (§37, §87):

- El manifiesto declara su idioma de forma explícita: `"language": "es"` o
  `"en"`.
- Su versión de corpus debe ser la de ese idioma.
- Todo documento o fila de asignación debe estar en ese idioma.
- Si no, la corrida **falla con un mensaje claro**. El idioma nunca se detecta
  desde el texto.

La usan `load_manifest` (toda ingesta) y el sorteo.
