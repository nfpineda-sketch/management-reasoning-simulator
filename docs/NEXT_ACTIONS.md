# Próximas acciones (una página)

Al cierre del ciclo 7, 2026-09-28. El detalle está en
`COLA_DECISIONES_AI_ADVISOR.md` («Cierre del ciclo 7») y en
`READINESS_PILOTO_RESIDENCIA.md`.

## Lo que Nicolás necesita hacer

1. **Autorizar, o no, el piloto formativo controlado** (TECHNICALLY READY,
   WITH CONDITIONS). Las condiciones:
   - uso formativo, con confirmación docente;
   - decidir o dejar fuera `acs_54m_inferior` (DF-20: A/B/C/D) y
     `acs_70f_left_main` (DF-23, fila 4a: «4a: aplicar el texto propuesto»);
   - TD-33, en trauma: «sólo la sangre repone el déficit de la regla de
     sobrecarga» (recomendado);
   - una prueba de humo en la base real.
2. **Piloto de validación español:** revisar los 18 documentos, reclutar a los
   6 médicos y enviar. Se mide contra `939978a`.
3. **Piloto inglés:**
   - incorporar los DOCX ingleses que están fuera del repositorio;
   - elegir su baseline **antes** de leer cualquier respuesta (candidatos en
     `validation/pilot_v1_en/manifests/pilot_manifest.json`).
4. **Revisar la propuesta del ciclo 8** del reporte final.
5. **Cuando pueda:** las filas 4b, 6, 7 y 8 de DF-23 (CLINICAL REVIEW).

## Lo que el AI Advisor puede hacer después (con un ciclo aprobado)

- **TD-29:** la condición «cuando/when» en las órdenes que no son sangre.
- **Los residuos del lector según su medición:** TD-14, TD-30 y TD-32.
- **TDFC completo**, aprobado y diferido intacto: TD1, F1, C1 y C3.
- **Aplicar la fila 4a, DF-20 y TD-33** apenas lleguen sus respuestas: una
  sesión corta cada una.

## Lo que esperamos

- **Los documentos de los médicos (ES y EN).** Se aplica MEASURE FIRST: primero
  contra el baseline de cada idioma y después contra los HARDENED BASELINES V1
  y V2.
- **Sus respuestas clínicas:** DF-20, DF-23 y TD-33.

## Qué bloquea un piloto con residentes

- **Técnicamente, nada.** TD-26, TD-21, C4 y PostgreSQL están resueltos.
- **Quedan las condiciones de arriba** y su autorización.

## Qué bloquea afirmar validez

- La fidelidad del lector con texto externo no está medida.
- El sistema no es un instrumento validado (NOT YET ESTABLISHED).
- Sólo produce evidencia observacional, confirmada por un docente.

## Qué no tocar todavía

- **Los baselines:**
  - el SPANISH PILOT BASELINE `939978a`, sus 18 DOCX y sus defectos
    conocidos;
  - el baseline inglés, hasta elegirlo antes de las respuestas.
- **SEALED y el scoring:** SEALED nunca. Tampoco los eventos críticos, el −3,
  D1–D5, el radar, DIRECT/PARTIAL ni la confirmación docente.
- **El lector, fuera de lo que mida el piloto.** Está congelado en el
  DEVELOPMENT HARDENED BASELINE V2.
- **La biblioteca POCUS:** es FUTURE ARCHITECTURE, no un bug.
