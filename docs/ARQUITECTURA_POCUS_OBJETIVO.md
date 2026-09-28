# Arquitectura POCUS objetivo · biblioteca de imágenes y videos reales

**Estado: FUTURE ARCHITECTURE.** Decisión docente del 2026-09-28, al aprobar el
ciclo 7.

- **No está implementada** y no se implementa en el ciclo 7: no hay esquema,
  almacenamiento, CDN, interfaz de carga ni selector de assets.
- **No es deuda técnica ni un bug.** Es una evolución deliberada desde los
  hallazgos POCUS en texto hacia assets de imagen y video reales validados.
- Fuente metodológica relacionada: `docs/ACEP_POCUS_FRAMEWORK.md`.

## En una tabla

| | |
|---|---|
| **CURRENT** | Informe POCUS escrito (`pocus_report.py`, `efast_report.py`) |
| **TARGET** | Biblioteca curada de imágenes y videos reales de ultrasonido |
| **SELECTION** | Metadata estructurada + requerimiento clínico del caso |
| **DEFAULT** | Un asset validado y reutilizable |
| **AI GENERATION** | Sólo como respaldo, y con revisión humana antes de entrar a la biblioteca |
| **OBSERVABLE NOW** | Indicación + interpretación clínica de un hallazgo descrito + integración al manejo |
| **OBSERVABLE WITH FUTURE VISUAL ASSET** | Agrega el reconocimiento o la interpretación directa de la imagen |
| **NOT OBSERVABLE WITHOUT ACQUISITION INTERACTION** | La adquisición de la imagen y el desempeño psicomotor |

## 1. El caso pide información, no un archivo

El caso no pide «use `ultrasound_video_003.mp4`». Pide, conceptualmente:

- aplicación: cardíaca/hemodinámica;
- vista: PLAX;
- hallazgo: función sistólica cualitativa del VI severamente reducida;
- calidad: adecuada;
- dificultad: moderada.

**CASE → POCUS REQUIREMENT → ASSET MATCHING → VALIDATED CLIP.** Así la
biblioteca puede cambiar o crecer sin reescribir la lógica clínica del caso.

## 2. Variabilidad sin cambiar el constructo

- Un mismo hallazgo puede tener varios clips validados equivalentes (clip A,
  B, C para una función del VI severamente reducida).
- La selección futura puede considerar el hallazgo, la severidad, la calidad,
  la dificultad y la compatibilidad clínica.
- **Dos modos:**
  - **STANDARDIZED ASSESSMENT MODE:** el o los assets validados quedan fijos
    (LOCKED) para todos los participantes. Misma versión del caso + misma
    versión del asset + mismo estado inicial.
  - **FORMATIVE / REPLAY MODE:** varios assets validados equivalentes que
    representan el mismo constructo.
- Esto separa la estandarización de la variabilidad. **No se afirma todavía**
  que produzca comparabilidad válida entre residentes, programas o países.

## 3. El asset validado es la fuente de verdad

- El asset validado es la fuente visual primaria. Su metadata describe **lo
  que se sabe que el asset muestra**.
- La revisión clínica ocurre al **curar y validar** el asset; después se
  reutiliza su metadata. Ningún modelo de IA mira el video en cada encuentro
  para volver a decidir qué muestra.
- Esto mejora el costo, la velocidad, la reproducibilidad y la confiabilidad
  clínica.

## 4. Metadata y procedencia que cada asset debe poder conservar

- ASSET ID, SOURCE, REVIEW STATUS, REVIEWER, VERSION;
- APPLICATION, VIEW, ANATOMY, FINDING, SEVERITY;
- IMAGE QUALITY, DIFFICULTY, CLINICAL COMPATIBILITY;
- ACEP COMPONENT(S), OBSERVABLE COMPONENT(S), LIMITATIONS;
- VALIDATION / REVIEW STATUS.

**Requisitos futuros** (sin diseñar ahora):

- Si un asset cambia, cada encuentro histórico sigue referenciando la versión
  que realmente se mostró.
- **Dificultad y calidad:** la metadata debe poder representar algo como
  OBVIOUS, MODERATE, SUBTLE y LIMITED / NON-DIAGNOSTIC, u otro esquema
  validado después. No se define ahora una escala.
- **No sólo imágenes perfectas.** El POCUS de urgencia incluye calidad
  variable, ventanas limitadas, hallazgos normales y anormales, patología sutil
  y estudios no diagnósticos. Pero todo asset usado para evaluar debe tener
  una interpretación conocida y un propósito educativo validado.
- **Material clínico real:** antes de incorporar cualquier imagen o video de
  pacientes reales se exigen desidentificación, derechos o permisos,
  procedencia y control de acceso. No se copia ni se importa material real
  ahora, ni se diseña todavía el sistema legal o de consentimiento.

## 5. Generación con IA

VALIDATED REAL LIBRARY ASSET → **primero**. AI-GENERATED ULTRASOUND → **sólo
como respaldo**. Un asset generado por IA nunca entra automáticamente a la
biblioteca validada:

GENERATION → HUMAN CLINICAL / ULTRASOUND REVIEW → APPROVAL → LIBRARY.

No se generan videos POCUS con IA para cada encuentro ni para cada pedido.

## 6. Qué evidencia podrá producir

- **Hoy (texto):** selección o indicación apropiada, interpretación clínica de
  los hallazgos entregados, integración al manejo y reevaluación cuando
  corresponde. No: adquisición, destreza psicomotora ni reconocimiento directo
  de la patología en una imagen.
- **Con assets visuales reales:** INDICATION → IMAGE RECOGNITION /
  INTERPRETATION → CLINICAL INTEGRATION → MANAGEMENT CONSEQUENCE →
  REASSESSMENT.
- **Aun entonces, la adquisición no se observa** salvo que la persona
  residente tenga que obtener la vista, posicionar un transductor, manipular
  la adquisición o interactuar con un simulador de adquisición. Un video
  preseleccionado no demuestra competencia de adquisición.
- **Procedencia:** la evidencia visual será una contribución distinta y
  trazable. La procedencia debe distinguir POCUS en texto de POCUS con asset
  visual, y la evidencia histórica en texto nunca se sustituye en silencio por
  evidencia visual.

## 7. Principio de diseño

**Mostrar la mínima información clínicamente plausible necesaria para crear la
oportunidad de observación buscada**, no todas las anormalidades que el
paciente tiene. El POCUS representa POCUS de medicina de urgencia, no
ecocardiografía consultiva completa. Un clip puede ser normal, limitado, no
diagnóstico o ambiguo si eso es coherente con el encuentro.

## 8. C14 y esta arquitectura

- El C14 actual se evalúa con la capacidad actual: POCUS en texto. Los 31
  casos no se reinterpretan con la arquitectura futura.
- Cuando exista la biblioteca visual, C14 se revisará aparte para distinguir
  indicación, reconocimiento o interpretación de la imagen, integración,
  consecuencia de manejo y reevaluación. Sin cambiar Objective Progress ni la
  meta de 50, y sin crear subpuntajes.

## 9. Fuentes externas de evidencia

Un mismo perfil longitudinal futuro podrá recibir unidades de evidencia del
simulador de encuentros clínicos, de simulación procedural, de observación en
el lugar de trabajo y de otras fuentes validadas. Este simulador no es toda la
evidencia de competencia. No se implementa ahora una arquitectura de ingesta
nueva (charter §107).
