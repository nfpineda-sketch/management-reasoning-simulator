# Piloto de validación v1 · paquete listo para distribuir

**Estado: PREPARADO, NO ENVIADO.** Nadie fue contactado y ningún documento se
distribuyó.

**DOCX STRUCTURALLY VERIFIED.** Los documentos se verificaron con python-docx
y con el lector real del producto (`manifests/docx_verification.json`). **No
se verificaron visualmente en Microsoft Word**: esa verificación queda para
usted.

## Qué es

- **Participantes y documentos.** Seis médicos de urgencia (EM01–EM06) reciben
  tres casos cada uno: 18 documentos Word en español.
- **Qué hacen.** Escriben en texto libre cómo manejarían al paciente.
- **Qué se hace con el texto.** Lo lee la página real del producto, y se
  compara con una anotación clínica ciega de lo que el médico quiso decir.
- **Qué se evalúa.** El **motor**: si entendió, ejecutó y registró bien lo
  escrito. **No se evalúa a los médicos** (§62).
- **Base.** Decisión docente DF-15, aprobada con modificaciones el 2026-09-28.

---

## FILES FOR NICOLÁS

### 1. Qué abrir en Word

- **Los 18 archivos de `documents/`**, uno por médico y caso.
- **Opcional:** las plantillas en blanco de `blank/`, sólo si piensa usar un
  reemplazo más adelante.

### 2. Qué enviar a cada médico

Envíe sólo los tres archivos de su carpeta.

| Médico | Archivos (carpeta `documents/EMxx/`) |
|---|---|
| EM01 | `EM01_C01_es.docx`, `EM01_C06_es.docx`, `EM01_C04_es.docx` |
| EM02 | `EM02_C01_es.docx`, `EM02_C06_es.docx`, `EM02_C02_es.docx` |
| EM03 | `EM03_C02_es.docx`, `EM03_C05_es.docx`, `EM03_C06_es.docx` |
| EM04 | `EM04_C02_es.docx`, `EM04_C05_es.docx`, `EM04_C03_es.docx` |
| EM05 | `EM05_C03_es.docx`, `EM05_C04_es.docx`, `EM05_C01_es.docx` |
| EM06 | `EM06_C03_es.docx`, `EM06_C04_es.docx`, `EM06_C05_es.docx` |

**La llave código ↔ persona.** Decida usted qué persona es EM01, EM02, etc.
Guarde esa llave **fuera del repositorio y sin compartirla**. Ninguno de estos
archivos pide ni guarda nombres.

**Médicos que se conocen.** Los dos médicos de un par comparten dos casos
(EM01 con EM02, EM03 con EM04, EM05 con EM06). Si dos participantes trabajan
juntos o suelen conversar casos, conviene que no queden en el mismo par.

### 3. Qué instrucciones copiar o adjuntar

- **El texto del mensaje:** `instructions/physician_instructions_es.md`, entre
  las dos líneas. Copie ese texto en el mensaje y complete lo que está entre
  corchetes: el nombre, los tres archivos y la fecha de devolución.
- **Las instrucciones de cada caso** ya van dentro de cada documento. No hay
  que adjuntar nada más.
- **El texto en inglés** (`physician_instructions_en.md`) es para la fase
  posterior, sólo con médicos que escriban naturalmente en inglés.

### 4. Qué **no** enviar

- **Nada fuera de `documents/EMxx/`.** Nunca vaya a un médico:
  - `assignment_matrix.csv`, que nombra los diagnósticos;
  - `manifests/`, `annotation/`, `KNOWN_DEFECTS.md`, `SPLIT_PROCEDURE.md` y
    este README;
  - `tools/` y `blank/`;
  - los documentos de otro médico.
- **No explique cómo lee el texto el simulador.** Nada de palabras que
  reconoce, errores conocidos ni frases de ejemplo (§37).

### 5. Qué verificar visualmente en Word (en cada documento)

1. **Que abra sin aviso de reparación.**
2. **La tabla del encabezado:** código de participante (EMxx), «Español», caso
   (C01…C06) y versión «VC2-ES».
3. **Las instrucciones:** breves y legibles, con la frase en negrita «Escriba
   naturalmente, como lo haría al manejar el paciente…».
4. **«El paciente»:** presentación, lo que dice el paciente, el monitor con
   «SpO₂» bien escrito, y peso y talla. Sin diagnóstico.
5. **El cuadro «Su manejo»:** amplio y con espacio para escribir.
6. **La redacción en español de los seis casos.** Viene de la traducción del
   banco (`case_text/es`). Su aprobación docente vive en la base de datos del
   despliegue y no pude comprobarla. **Su lectura en Word es esa aprobación**
   para el piloto.
7. **Que se pueda escribir en el cuadro.** Pruebe escribir y **cierre sin
   guardar**, o pruebe en una copia, para que el archivo enviado quede como
   está.

El contenido ya se revisó por programa:

- no hay spoilers ni diagnóstico final;
- no hay palabras internas del sistema;
- se puede rellenar, guardar y releer;
- la ingesta conserva el orden.

### 6. Qué hacer cuando le devuelvan los documentos

1. **No los abra.** Guárdelos tal como llegan en una carpeta **fuera del
   repositorio**, por ejemplo `~/piloto_v1/devueltos/`, con el nombre con que
   se enviaron.
2. **Anote fuera del repositorio** el tiempo que cada médico dijo haber
   tomado y sus comentarios sobre el formato, por ejemplo en
   `~/piloto_v1/notas.txt`.
3. **Haga el sorteo.** Cuando estén todos, o en la fecha de cierre que fije,
   siga `SPLIT_PROCEDURE.md`: un comando, o pídale a Claude que lo corra con el
   commit de `PILOT_BASELINE.md`. El sorteo no lee el texto.
4. **Siga el orden de trabajo.** Recién después: anotación ciega, motor y
   adjudicación, en el orden de `annotation/adjudication_guide.md`.

### 7. Dónde guardar los documentos devueltos

| Qué | Dónde | Por qué |
|---|---|---|
| Los devueltos, tal como llegan | `~/piloto_v1/devueltos/`, fuera del repositorio | nadie los lee antes del sorteo |
| DEVELOPMENT, después del sorteo | `~/piloto_v1/corpus/development/`; puede copiarse a `local-data/` de una sesión (git la ignora) | es con lo que se trabaja |
| **SEALED**, después del sorteo | `~/piloto_v1/corpus/sealed/`, **sólo en su equipo** | no entra al repositorio ni a una sesión de desarrollo hasta que haya una versión candidata congelada (§42) |
| La llave código ↔ persona | fuera del repositorio, sin compartir | privacidad |

---

## Mapa del paquete

```
validation/pilot_v1/
  README.md                        este archivo
  assignment_matrix.csv            quién recibe qué caso (NO ENVIAR: nombra diagnósticos)
  SPLIT_PROCEDURE.md               sorteo development/sealed, definido y no ejecutado
  KNOWN_DEFECTS.md                 defectos conocidos del baseline
  PILOT_BASELINE.md                commit, versión, fecha y pruebas del baseline
  documents/EM01 … EM06/           los 18 documentos para enviar
  blank/                           plantillas en blanco ES/EN, para reemplazos o para la fase en inglés
  instructions/                    texto del mensaje, ES y EN
  annotation/                      plantilla, guía de anotación y guía de adjudicación
  manifests/
    pilot_manifest.json            casos, pares, asignación y reglas
    documents.json                 cada documento: versión, SHA-256 y fuente del texto del caso
    docx_verification.json         verificación estructural, documento por documento
    known_defects.json             los defectos conocidos, como dato
  tools/README.md                  los comandos (la herramienta es tools_validation_corpus.py)
```

## Cómo se armó la asignación (§36)

| Par | Comparten | Extra de cada uno |
|---|---|---|
| P1 · EM01, EM02 | C01 asma, C06 trauma | EM01: C04 anafilaxia · EM02: C02 neumonía |
| P2 · EM03, EM04 | C02 neumonía, C05 cólico renal con alta | EM03: C06 trauma · EM04: C03 HDA |
| P3 · EM05, EM06 | C03 HDA, C04 anafilaxia | EM05: C01 asma · EM06: C05 cólico renal |

- **Cada caso tiene 3 respuestas independientes.**
- **Cada médico tiene exactamente un caso sin shock** (C01 o C05) y dos en
  shock, y nunca las dos hemorragias juntas.
- **Están representados:**
  - el alta (C05);
  - los procedimientos e intervenciones (C06, C03);
  - las órdenes múltiples y la reevaluación, en los seis casos.
- **Ambos subconjuntos tienen los seis casos.** Los dos miembros de cada par
  comparten dos casos y el sorteo separa al par.

## Carga estimada (§35)

- **Por caso:** unos 10–15 minutos. Cada documento trae sólo la información de
  llegada y un cuadro de respuesta, sin evolución.
- **Total por médico:** 30–45 minutos.

El piloto lo mide con el tiempo que informe cada médico.

## Lo que no está hecho, a propósito

- **Contacto y envíos.** No se contactó a nadie, no se enviaron correos ni se
  distribuyó nada.
- **Sorteo.** No se hizo; se hace al volver los documentos.
- **Respuestas.** No hay respuestas, anotaciones ni validación. Nada se inventó
  ni se simuló.
- **Inglés.** No hay documentos en inglés asignados: esa fase viene después.
