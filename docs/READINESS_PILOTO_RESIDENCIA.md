# Readiness del piloto con residentes (ciclo 9)

Instrucción docente del 2026-09-29, ciclo 9 (§77, §78, §79 y §125). Actualiza
la versión del ciclo 8 después de TD-39, TD-34, TD-36, TD-33, DF-20 y DF-23 4a,
y del congelamiento de la DEVELOPMENT PRE-VALIDATION BASELINE V3
(`validation/BASELINES.md`).

**Lo nuevo del ciclo 9: la pregunta se separa en dos.**

- **A. ENGINE TECHNICAL READINESS:** si el motor está técnicamente listo.
- **B. EXTERNAL LANGUAGE FIDELITY EVIDENCE:** si hay evidencia de que el lector
  entiende el lenguaje de médicos externos.

Puede ser A = YES y B = NOT YET MEASURED. Así está hoy.

**Esto es readiness técnica, no validez metodológica.**

- Lo implementado no está validado (CURRENTLY IMPLEMENTED ≠ VALIDATED).
- Las cifras de los conjuntos internos (ciegos, adversariales, independientes)
  son INTERNAL DEVELOPMENT DATA y sirven como corpus de regresión, no como
  evidencia de generalización externa (charter §116–§117).

## Respuestas

| Pregunta | Respuesta | Por qué |
|---|---|---|
| **A. ENGINE TECHNICAL READINESS** | **YES** | TD-39, TD-34, TD-36 y TD-33 corregidos y probados; DF-20 cerrado y TDFC completo en los 31 casos; ningún CRITICAL conocido sin resolver; la suite completa y las 56 regresiones, verdes sobre V3. El HIGH que queda (KD-28, TD-14) es fricción: el lector pregunta y no ejecuta nada |
| **B. EXTERNAL LANGUAGE FIDELITY EVIDENCE** | **NOT YET MEASURED** | Ningún documento externo se ha leído. La primera medición española se hace contra `939978a`; la inglesa, contra el baseline que el docente elija antes de leer respuestas (recomendado: V3) |
| **CONTROLLED FORMATIVE RESIDENCY PILOT READY?** | **TECHNICALLY READY (A = YES), CON LIMITACIONES EXPLÍCITAS Y CONFIRMACIÓN DOCENTE.** Falta su autorización | No se retrasa el uso formativo por la validación del lector (§77), siempre que las limitaciones sean explícitas y cada rúbrica la confirme un docente |
| **EXTERNAL VALIDATION PILOT READY?** | **SÍ (tooling listo)** | Inventario RAW con SHA-256, metadatos por nombre, copia de trabajo, frontera de respuesta, duplicados y conflictos, separación ES/EN, sorteo y anotación con procedencia (`docs/VALIDACION_EXTERNA_PREPARACION.md`). Ensayado con documentos en blanco y ficticios |
| **VALIDATED ASSESSMENT INSTRUMENT?** | **NO / NOT YET ESTABLISHED** | Sin datos externos medidos. El sistema produce evidencia observacional, confirmada por un docente; no certifica competencia |

## Condiciones para el piloto formativo controlado

1. **Uso formativo.** Ningún juicio sale del Trace solo, y cada rúbrica la
   confirma un docente. Vale hasta que el piloto de validación mida el lector
   con texto externo.
2. **Una prueba de humo en la base real antes de empezar:** crear una cuenta,
   jugar un encuentro, confirmar una rúbrica y ver el perfil. PostgreSQL se
   verificó en un clúster local descartable (ciclo 7); staging no se tocó.
3. **El español de `acs_70f_left_main`.** Su POCUS cambió (DF-23 4a). Si su
   texto en español estaba aprobado en la base desplegada, vuelve a esperar la
   revisión docente: la aprobación es por versión exacta y no se registra en
   nombre de nadie.
4. **Las limitaciones conocidas, para el docente** (no son instrucciones para
   el residente): `validation/KNOWN_DEFECTS_V3.md`. Ninguna es CRITICAL.

**Ya no son condiciones:** DF-20 (cerrado; `acs_54m_inferior` se usa como
está), la fila 4a (aplicada) y TD-33 (aplicado; la sangre ya no «hace daño»
tras reponer con cristaloide).

## Qué decir a los residentes

Sólo lo clínico y las limitaciones inevitables del simulador (§78, §79). No
hay una lista de «escriba X, no Y».

- **Escriba sus órdenes como en una ficha clínica:** qué, dosis, vía y, si
  corresponde, cuándo.
- **Si el simulador no entiende una orden, se la pregunta.** Nada se ejecuta
  sin reconocerse; responda la pregunta o reescriba la orden.
- **Un plan para más tarde o condicional queda registrado y no se realiza
  solo.** El tiempo del simulador avanza con sus órdenes y reevaluaciones:
  cuando llegue el momento, ordénelo.
- **Algunos fármacos y medidas se registran sin efecto fisiológico modelado.**
  La sala lo dice cada vez.

**Se retiraron** las tres instrucciones compensatorias del ciclo 8, porque sus
defectos se corrigieron:

- escribir en minutos el tiempo de una reevaluación (TD-34);
- escribir primero quién dio lo recibido en ruta (TD-36);
- escribir el alta sólo cuando corresponda darla (TD-39).

## Lo que queda (ninguno es BLOCKER técnico)

| Clase | Área | Qué | Referencia |
|---|---|---|---|
| HIGH | Fricción del lector | Mucho vocabulario fuera del lector se retiene con una pregunta. Es honesto, pero cuesta turnos | KD-28 · TD-14 |
| MEDIUM | Lector | Pérdidas sin aviso fuera de las clases corregidas: «d/c home», un alta escrita como intención, «Observe 6 h» solo, lo que sigue a una reevaluación, abreviaturas en una lista sin verbo | KD-16 a KD-19, KD-26 |
| MEDIUM | Lector | Condiciones en inglés con «we» o «and», y sobre «SatO2», corren ahora; algunas altas no se leen («OK to send home») | KD-29 · TD-40 |
| MEDIUM | Lector · motor | Repetir la adrenalina que dio el SAMU se retiene con una pregunta; un fragmento no reconocido retiene la adrenalina escrita con él | KD-21, KD-24 |
| MEDIUM | Tamizaje | El tamizaje no cita un tratamiento previo registrado; el docente lo ve en el Trace | KD-31 |
| MEDIUM | Consistencia clínica | Las filas 4b, 6, 7 y 8 de DF-23 | CLINICAL REVIEW |
| MEDIUM | Integridad | I-F18 y los demás de TD-18 quedaron fuera de DF-24 | TD-18 |
| MEDIUM | Escala | La cola docente es lineal: 3 s con 1000 encuentros pendientes | TD-09 |
| LOW | Sala | Un envío que sólo trae un plan o historia agrega el aviso genérico | KD-25 · TD-38 |
| LOW | Idioma y observabilidad | La razón de C14 en inglés en el portal docente; el commit por turno | TD-07, TD-10 |

## Qué cambió desde el ciclo 8

| En el ciclo 8 | Ahora |
|---|---|
| HIGH: un alta con plazo o tras una observación corría ahora (TD-39) | **Corregido:** es un plan de destino, registrado, que no cierra el encuentro (C-2026-09-29-01, -07) |
| HIGH: «Reevaluar en 1 h» corría a los 0 minutos (TD-34) | **Corregido:** 60 minutos en el lector, el motor, el reloj y el Trace (C-2026-09-29-02, -07) |
| HIGH: «Aspirin 300 mg given by EMS» se daba de nuevo (TD-36) | **Corregido:** es historia, con qué, dosis, vía, quién y cuándo (C-2026-09-29-03, -07) |
| HIGH: en trauma, la sangre tras el cristaloide disparaba la sobrecarga (TD-33) | **Corregido** por decisión docente (C-2026-09-29-04) |
| HIGH: `acs_54m_inferior`, el VD contradicho (TD-01, DF-20) | **Cerrado sin cambios** por decisión docente; TDFC declarado (C-2026-09-29-05) |
| DF-23 4a: «No B-lines» frente a la congestión | **Aplicado** (C-2026-09-29-06) |
| Condición 5: tres instrucciones compensatorias | **Retiradas** |

## Lo que este documento no afirma

- **No afirma una evaluación validada.** Tampoco que el simulador pruebe
  competencia, prediga el desempeño clínico o sea comparable entre programas.
- **No afirma la fidelidad externa del lector:** no está medida.
- **No reemplaza al piloto de validación.** La primera medición humana en
  español se hace contra el SPANISH PILOT BASELINE `939978a`.
- **La regla cuando lleguen datos humanos es MEASURE FIRST:** BASELINE →
  MEASUREMENT → ANNOTATION → ADJUDICATION → ERROR CLASSIFICATION →
  PRIORITIZATION → APPROVED FIX.
