# Próximas acciones (una página)

Al cierre del ciclo 9, 2026-09-29. El detalle está en
`COLA_DECISIONES_AI_ADVISOR.md` («Cierre del ciclo 9»), en
`READINESS_PILOTO_RESIDENCIA.md`, en `VALIDACION_EXTERNA_PREPARACION.md` y en
`validation/BASELINES.md`.

## Lo que Nicolás necesita hacer

1. **Elegir el baseline inglés antes de leer cualquier respuesta inglesa.**
   Recomendado: **V3** (DEVELOPMENT PRE-VALIDATION BASELINE V3, en
   `validation/BASELINES.md`). Una línea basta: «inglés: V3» o «inglés: V2».
2. **Entregar los documentos cuando estén listos,** como dice
   `VALIDACION_EXTERNA_PREPARACION.md`: los originales fuera del repositorio,
   una carpeta por idioma, y la frase «BEGIN EXTERNAL VALIDATION INGESTION».
3. **Autorizar, o no, el piloto formativo controlado.** A (motor) = YES; B
   (fidelidad externa) = NOT YET MEASURED. Antes, una prueba de humo en la base
   real.
4. **Si el español de `acs_70f_left_main` estaba aprobado en la base
   desplegada,** revisarlo de nuevo: su POCUS cambió (fila 4a).
5. **Decisiones que siguen abiertas, cuando pueda:**
   - DF-23, filas 4b, 6, 7 y 8 (CLINICAL REVIEW);
   - KD-02 y TD-35: ¿preguntar lo que una lista nombra sin verbo?;
   - KD-15, la regla de medidas combinadas (resto de TD-31) y DC3;
   - las dudas residuales de TDFC y si las composiciones heredan TD/F/C;
   - KD-31: si el tamizaje debe citar un tratamiento previo registrado;
   - pantallas por rol (`EXPERIENCIA_POR_ROL.md`): si el foco de aprendizaje se
     sigue mostrando al cerrar el encuentro, antes de la revisión docente; qué
     entra en la Fase 2 (AI Longitudinal Review especificada, notas privadas,
     auditoría de cuentas); y las traducciones que aún se piden al cargar una página.

## Lo que el AI Advisor hará cuando lleguen los documentos

Sólo tras «BEGIN EXTERNAL VALIDATION INGESTION», en este orden: identificar el
idioma, inventariar y fijar el SHA-256 de lo recibido, revisar metadatos,
detectar faltantes, duplicados y conflictos, crear las copias de trabajo,
verificar el manifiesto, congelar la versión del corpus, sortear
DEVELOPMENT/SEALED y, sólo entonces, la anotación de referencia a ciegas,
hecha por personas.

## Lo que esperamos

- **Los documentos de los médicos, español e inglés, como dos corpus.** MEASURE
  FIRST: el español contra `939978a`; el inglés contra el baseline elegido.
  Sólo en DEVELOPMENT se compara después `939978a`, V1, V2 y V3.
- **Nada se corrige antes de medir.** Los defectos conocidos se etiquetan
  (`validation/KNOWN_DEFECTS_V3.md`); no salen de las métricas.

## Qué no tocar

- **Los baselines:** `939978a` y sus 18 DOCX, el ENGLISH VALIDATION BASELINE
  `ec1c77f`, V1, V2 y V3; la lista de defectos del piloto (versión 2).
- **El lector congelado en V3:** lo nuevo MEDIUM o LOW es deuda técnica; sin
  otro conjunto ciego interno (charter §116–§117).
- **SEALED y el scoring:** SEALED nunca. Tampoco los eventos críticos, el −3,
  D1–D5, el radar, DIRECT/PARTIAL, C4 ni la confirmación docente.
- **La biblioteca POCUS:** es FUTURE ARCHITECTURE, no un bug.

## Qué bloquea afirmar validez

- La fidelidad del lector con texto externo no está medida.
- El sistema no es un instrumento validado (NOT YET ESTABLISHED).
- Sólo produce evidencia observacional, confirmada por un docente.
