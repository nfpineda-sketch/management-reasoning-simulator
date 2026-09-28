# Próximas acciones (una página)

Al cierre del ciclo 8, 2026-09-28. El detalle está en
`COLA_DECISIONES_AI_ADVISOR.md` («Cierre del ciclo 8»), en
`READINESS_PILOTO_RESIDENCIA.md` y en `CICLO8_LECTOR.md`.

## Lo que Nicolás necesita hacer

1. **Autorizar, o no, el piloto formativo controlado** (TECHNICALLY READY,
   WITH CONDITIONS). Las condiciones:
   - uso formativo, con confirmación docente;
   - decidir o dejar fuera `acs_54m_inferior` (DF-20: A/B/C/D) y
     `acs_70f_left_main` (DF-23, fila 4a: «4a: aplicar el texto propuesto»);
   - TD-33, en trauma: «sólo la sangre repone el déficit de la regla de
     sobrecarga» (recomendado);
   - una prueba de humo en la base real;
   - decir a los residentes que escriban en minutos el tiempo de una
     reevaluación (TD-34), y lo recibido en ruta con quien lo dio delante
     (TD-36).
2. **Piloto de validación español:** revisar los 18 documentos, reclutar a los
   6 médicos y enviar. Se mide contra `939978a`.
3. **Piloto inglés:**
   - incorporar los DOCX ingleses que están fuera del repositorio;
   - elegir su baseline **antes** de leer cualquier respuesta (candidatos en
     `validation/pilot_v1_en/manifests/pilot_manifest.json`, con el V2 ya
     nombrado por su commit, `9d2cd9e`);
   - KD-05 («OK to discharge») está corregido en el lector de desarrollo, pero
     sigue presente en los candidatos registrados.
4. **Decisiones del reporte final del ciclo 8:**
   - KD-02 y TD-35: ¿preguntar lo que una lista nombra sin verbo?;
   - KD-15;
   - la regla de medidas combinadas (resto de TD-31);
   - DC3;
   - las dudas residuales de TDFC;
   - si las composiciones de hipoglicemia heredan TD/F/C.
5. **Cuando pueda:** las filas 4b, 6, 7 y 8 de DF-23 (CLINICAL REVIEW).

## Lo que el AI Advisor puede hacer después (con un ciclo aprobado)

- **TD-34:** «h» y «hr» como horas en una reevaluación. Se preguntan los
  minutos, como hoy con «hora». Es una línea, con A–J.
- **Los residuos del lector según su medición:**
  - TD-14 y TD-35: vocabulario y listas sin verbo;
  - TD-36: un relato leído como orden («X given by EMS» se da de nuevo);
  - TD-37: la receta del alta en lista.
- **TD-38:** que la sala muestre un plan registrado sin el aviso genérico.
- **Aplicar la fila 4a, DF-20 y TD-33** apenas lleguen sus respuestas: una
  sesión corta cada una.

## Lo que esperamos

- **Los documentos de los médicos (ES y EN).** Se aplica MEASURE FIRST: primero
  contra el baseline de cada idioma y después contra los HARDENED BASELINES V1
  y V2.
- **Sus respuestas clínicas:** DF-20, DF-23 y TD-33.

## Qué bloquea un piloto con residentes

- **Técnicamente, nada.** TD-26, TD-21, C4 y PostgreSQL se resolvieron en el
  ciclo 7. El ciclo 8 corrigió TD-29 a TD-32 y KD-05, y aplicó TDFC.
- **Quedan las condiciones de arriba** y su autorización.

## Qué bloquea afirmar validez

- La fidelidad del lector con texto externo no está medida.
- El sistema no es un instrumento validado (NOT YET ESTABLISHED).
- Sólo produce evidencia observacional, confirmada por un docente.

## Qué no tocar todavía

- **Los baselines:**
  - el SPANISH PILOT BASELINE `939978a`, sus 18 DOCX y sus defectos
    conocidos;
  - el baseline inglés, hasta elegirlo antes de las respuestas;
  - el manifiesto de defectos conocidos (versión 2), hasta que haya un
    baseline nuevo.
- **SEALED y el scoring:** SEALED nunca. Tampoco los eventos críticos, el −3,
  D1–D5, el radar, DIRECT/PARTIAL ni la confirmación docente.
- **El lector, fuera de lo que mida el piloto.** Las mediciones se hacen contra
  los baselines registrados; el lector de desarrollo del ciclo 8 es una
  referencia, no un baseline.
- **La biblioteca POCUS:** es FUTURE ARCHITECTURE, no un bug.
