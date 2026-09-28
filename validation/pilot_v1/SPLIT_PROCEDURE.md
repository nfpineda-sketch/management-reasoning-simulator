# Procedimiento development / sealed del piloto

Definido **antes** de recibir los documentos (§18, §41). El sorteo **no está
hecho**: se hace una sola vez, cuando vuelvan los documentos y antes de que
nadie los abra.

## Principio

- **Qué se asigna.** Se asigna el **médico**: todos sus documentos van al mismo
  subconjunto, así que el estilo de un médico no cruza el límite. La
  herramienta lo exige (`load_manifest`).
- **Estratificación por par.** Los dos médicos de un par comparten dos casos:
  - P1 (EM01, EM02): C01 y C06;
  - P2 (EM03, EM04): C02 y C05;
  - P3 (EM05, EM06): C03 y C04.
- **El sorteo.** Dentro de cada par, uno va a DEVELOPMENT y el otro a SEALED.
- **El resultado.** Cada subconjunto recibe 3 médicos y 9 documentos, con los
  seis casos presentes en ambos.
- **Nada depende de leer.** El sorteo usa sólo el nombre y el SHA-256 de los
  bytes de cada archivo, nunca su texto. Nadie puede ver qué tan difíciles son
  las respuestas antes de asignarlas.

## La regla (determinística, reproducible y auditable)

1. **La semilla.** Es el SHA-256 de estas líneas, en este orden:
   - `pilot VALIDATION_PILOT_V1`;
   - `baseline <commit del baseline del piloto>`;
   - una línea por archivo devuelto, `<nombre> <sha256>`, ordenadas por nombre.
2. **La asignación.** Para el par número *k* (P1, P2, P3), se mira el dígito
   hexadecimal *k* de la semilla:
   - **par:** el primer médico del par va a DEVELOPMENT y el segundo a SEALED;
   - **impar:** al revés.

La semilla no existe antes de que existan los documentos. Cualquiera con los
mismos archivos y el mismo commit obtiene el mismo sorteo. `split.json` guarda
las líneas, la semilla y el resultado de cada par.

## Pasos

1. **Guardar sin abrir.** Guarde cada archivo devuelto, sin abrirlo, en **una
   carpeta fuera del repositorio**, por ejemplo `~/piloto_v1/devueltos/`.
2. **Revisar el nombre.** Si alguien cambió el nombre, devuélvale el nombre con
   que se envió (`EM01_C01_es.docx`). Renombrar no abre el archivo.
3. **Declarar el cierre.** Cuando estén todos, o al llegar la fecha de cierre
   que usted fije, corra:

   ```
   python tools_validation_corpus.py split \
     --pilot validation/pilot_v1/manifests/pilot_manifest.json \
     --returned ~/piloto_v1/devueltos \
     --baseline <commit de PILOT_BASELINE.md> \
     --corpus ~/piloto_v1/corpus \
     --collected-on AAAA-MM-DD
   ```
4. **Lo que escribe la herramienta** en `~/piloto_v1/corpus/`:
   - `split.json`, el sorteo completo;
   - `development/` y `sealed/`, con las copias de los archivos;
   - `manifest.json`, listo para `ingest`.

   Se niega a correr si la carpeta está dentro del repositorio.
5. **Opcional, después del sorteo.** Quite el nombre del autor de las
   propiedades del archivo (Word: *Archivo > Información > Inspeccionar
   documento*). La ingesta avisa si queda y nunca lo lee. El sorteo ya registró
   el SHA-256 de lo recibido.
6. **Dónde queda cada subconjunto.**
   - **Development:** puede trabajarse en el equipo del custodio o copiarse a
     `local-data/` de una sesión, carpeta que git ignora.
   - **Sealed:** no entra al repositorio ni a una sesión de desarrollo hasta que
     haya una versión candidata congelada (§42).

## Documentos que faltan o llegan tarde (reglas fijadas ahora)

- **Un solo sorteo.** Si al cierre falta algo, se sortea con lo que llegó y
  `split.json` lista lo que falta. La herramienta no vuelve a sortear sobre
  otros archivos.
- **Un documento que llega tarde** va al subconjunto de su médico, ya sorteado.
  Se agrega su fila a `manifest.json` con ese subconjunto.
- **Un médico que no devuelve nada** deja su lugar vacío. Si se incorpora un
  reemplazo:
  - recibe un código nuevo (EM07…) y los mismos tres casos;
  - hereda el subconjunto del médico que reemplaza;
  - se anota en `manifest.json` con la nota «replaces EMxx».
- **Un documento que no se puede leer** sigue en su subconjunto, y se le puede
  pedir de nuevo al mismo médico.

## Después

- **Una entrada sealed usada para corregir el sistema deja de ser sealed.** Se
  registra en `retired_entries` de `manifest.json` (id, fecha y motivo) como
  RETIRED FROM VALIDATION (§42).
- **El orden siguiente es fijo:** anotación ciega, luego motor, luego
  adjudicación. Está en `annotation/adjudication_guide.md` (§74).
