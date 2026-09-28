# Herramientas del piloto

El piloto usa el pipeline del validation corpus, sin duplicarlo:

```
DOCX → TEXTO → PÁGINA REAL DEL PRODUCTO → SALIDA ESTRUCTURADA → REPORTE
```

- `validation_corpus.py`: plantilla, lectura, manifiesto, sorteo, hojas y
  métricas.
- `tools_validation_corpus.py`: línea de comandos.

Todo es determinístico, no llama a ningún modelo y no contacta a nadie.

## Regenerar los documentos

Hágalo sólo si cambia el texto de un caso o la plantilla. Una prueba
(`test_pilot_package.py`) avisa si los documentos ya no coinciden con el
generador.

```
python tools_validation_corpus.py templates --pilot validation/pilot_v1/manifests/pilot_manifest.json --out validation/pilot_v1/documents
python tools_validation_corpus.py templates --out validation/pilot_v1/blank --language both
```

**Para un reemplazo o un médico de la fase en inglés.** El código se completa
al generar el documento:

```
python tools_validation_corpus.py templates --out DIR --language es --case C01 --case C06 --case C04 --participant EM07
```

## Cuando vuelvan los documentos

Las carpetas `CORPUS` y `SALIDA` van **fuera del repositorio**. Development
puede ir en `local-data/`; sealed, nunca.

1. **Sorteo** (`../SPLIT_PROCEDURE.md`):

   ```
   python tools_validation_corpus.py split --pilot validation/pilot_v1/manifests/pilot_manifest.json --returned DEVUELTOS --baseline SHA --corpus CORPUS --collected-on AAAA-MM-DD
   ```
2. **Ingesta.** Escribe `entries.json`, `annotation.csv` y
   `annotation_second.csv` (el 20 % fijo):

   ```
   python tools_validation_corpus.py ingest --corpus CORPUS --subset development --out SALIDA_DEV
   ```
3. **Anotación a ciegas** (`../annotation/annotation_guide.md`).
4. **El motor.** Cada entrada pasa por la página real, sin clave de proveedor.
   Corra en el commit del baseline (`../PILOT_BASELINE.md`):
   `engine_output.json` registra el commit y si había cambios sin guardar.

   ```
   python tools_validation_corpus.py run --out SALIDA_DEV --seed 3000
   ```
5. **Adjudicación** (`../annotation/adjudication_guide.md`):

   ```
   python tools_validation_corpus.py adjudicate --out SALIDA_DEV --second SALIDA_DEV/annotation_second.csv
   python tools_validation_corpus.py report --out SALIDA_DEV --second SALIDA_DEV/annotation_second.csv
   ```

   Después de resolver los desacuerdos, repita los dos comandos sin
   `--second`.
6. **Sealed.** Recién con una versión candidata congelada. Se usan los mismos
   comandos con `--subset sealed` y una carpeta de salida fuera del
   repositorio. La consola muestra sólo agregados.
