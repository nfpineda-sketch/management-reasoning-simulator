# Readiness del piloto con residentes (ciclo 8)

Instrucción docente del 2026-09-28, ciclo 7 (§96, §98.16 y §99). Actualiza la
versión del ciclo 6 después de TD-21, TD-26, C7-06, C4, C14, DF-24 y
PostgreSQL.

**Ciclo 8 (2026-09-28).** Las tres respuestas no cambian. Cambia lo que queda:

- **Corregidos:** TD-29 («cuando/when» ya guarda el plan), TD-30, la
  adrenalina IM de TD-31, TD-32 y KD-05 (`docs/CICLO8_LECTOR.md`).
- **TDFC aplicado:** TD1, F1, C1 y C3 declarados caso por caso, como C14. La
  transición sólo queda donde falta una decisión.
- **Hallado y no corregido, igual que antes del ciclo:**
  - «Reevaluar en 1 h» corre a los 0 minutos (TD-34);
  - «Aspirin 300 mg given by EMS» da la dosis de nuevo (TD-36).

  Los dos se suman a la condición 5.

**Esto es readiness técnica, no validez metodológica.**

- Lo implementado no está validado (CURRENTLY IMPLEMENTED ≠ VALIDATED).
- El sistema puede estar técnicamente listo para pilotear sin estar validado
  como instrumento de evaluación.
- Las cifras de los conjuntos ciegos son INTERNAL DEVELOPMENT DATA.

## Tres respuestas

| Pregunta | Respuesta | Por qué |
|---|---|---|
| **A. EXTERNAL VALIDATION PILOT READY?** | **SÍ (tooling listo).** Falta lo del docente | Español: 18 documentos, anotación, split y SPANISH PILOT BASELINE `939978a` intacto. Inglés: separado (EM07–EM12), preparado y no enviado; su baseline se elige antes de leer respuestas. Falta revisar los documentos, reclutar y enviar |
| **B. CONTROLLED FORMATIVE RESIDENCY PILOT READY?** | **TECHNICALLY READY, WITH CONDITIONS** (abajo) | Los cuatro bloqueos técnicos del ciclo 6 están resueltos: TD-26, TD-21, C4 y PostgreSQL. Lo que queda es metodológico, o son condiciones de uso |
| **C. VALIDATED ASSESSMENT INSTRUMENT?** | **NO / NOT YET ESTABLISHED** | Sin datos externos medidos. El sistema produce evidencia observacional, no certificación ni competencia |

## Condiciones para el piloto formativo controlado

1. **Uso formativo.** Ningún juicio sale del Trace solo, y cada rúbrica la
   confirma un docente. Vale hasta que el piloto de validación mida el lector
   con texto externo (DF-15).
2. **Casos con datos que se contradicen:** decidir o dejar fuera del piloto.
   - `acs_54m_inferior`: su C14 ya es NO, pero el VD sigue contradicho entre el
     caso y el POCUS (DF-20).
   - `acs_70f_left_main`: «No B-lines» frente a la congestión (DF-23, fila 4a).
3. **Trauma:** avisar al docente, o decidir TD-33 antes de empezar.
   - Tras reponer con cristaloide, transfundir muestra una sobrecarga que no
     corresponde.
   - No es un evento crítico ni toca el puntaje.
4. **Una prueba de humo en la base real antes de empezar:** crear una cuenta,
   jugar un encuentro, confirmar una rúbrica y ver el perfil.
   - PostgreSQL se verificó en un clúster local descartable.
   - Staging no se tocó, como se instruyó.
5. **Decir a los residentes cómo escribir mejor:**
   - una orden por línea, con su verbo;
   - «si…» o «cuando…» para una orden condicional: desde el ciclo 8 las dos
     la guardan como plan;
   - el tiempo de una reevaluación en minutos («reevaluar en 60 min»): «en
     1 h» todavía reevalúa sin que pase el tiempo (TD-34);
   - lo recibido en ruta con quien lo dio delante («el SAMU dio aspirina 300
     mg»): «Aspirin 300 mg given by EMS» se da de nuevo (TD-36).

## Bloqueos del ciclo 6, reevaluados (§96)

| Bloqueo del ciclo 6 | Estado | Tipo |
|---|---|---|
| TD-26: pérdidas sin aviso de hemoderivados | **Resuelto por clase.** En los conjuntos medidos quedan 0 pérdidas reales y 0 ejecuciones falsas. Quedan residuos LOW (TD-32) | Era técnico |
| TD-21: sobrecarga falsa al transfundir una hemorragia activa | **Resuelto** con el principio D (C-2026-09-28-12) | Era técnico |
| C4: valorable por la transición | **Resuelto:** C4 = NO en todo el entorno (C-2026-09-28-10) | Era técnico |
| PostgreSQL no probado | **Verificado** sobre el candidato final, en un clúster local descartable, y borrado. Staging no se tocó | Era técnico |
| La fidelidad del lector con texto externo no está medida | **Sigue sin medirse** | **METHODOLOGICAL LIMITATION.** No impide un piloto formativo controlado; sí impide afirmaciones de alto impacto (HIGH-STAKES ASSESSMENT CLAIMS) |

## Lo que queda (ninguno es BLOCKER técnico)

| Clase | Área | Qué | Referencia |
|---|---|---|---|
| HIGH | Lector | «Reevaluar en 1 h» o «Reassess in 1 h» reevalúa a los 0 minutos, sin aviso; «1 hora» pregunta los minutos | TD-34 |
| HIGH | Lector | Una dosis escrita antes de quien la dio se da de nuevo («Epinephrine 0.5 mg IM given by EMS»); con el equipo como sujeto se pregunta | TD-36 |
| HIGH | Fricción del lector | Mucho se retiene con una pregunta. Es honesto, pero cuesta turnos. En TD-26 las retenciones bajaron a la mitad | TD-14 |
| HIGH | Caso clínico | `acs_54m_inferior`: el VD contradicho | TD-01 · DF-20 |
| HIGH | Motor · trauma | Tras reponer con cristaloide, transfundir dispara la sobrecarga | TD-33 |
| MEDIUM | Lector | En una lista sin verbo, un examen abreviado o un nombre comercial que el lector no conoce se pierde sin aviso («CBC coags», «protonix 80 IV») | TD-35 · KD-02 |
| MEDIUM | Flujo docente | TDFC aplicado en el ciclo 8: TD1, F1, C1 y C3 sólo se valoran donde el caso ofrece la oportunidad. `acs_54m_inferior`, los casos generados y PS001 conservan la transición | DF-20, DF-12 |
| MEDIUM | Integridad | I-F18 y los demás de TD-18 quedaron fuera de DF-24 | TD-18 |
| MEDIUM | Consistencia clínica | Las filas 4a, 4b, 6, 7 y 8 de DF-23 | CLINICAL REVIEW |
| MEDIUM | Escala | La cola docente es lineal: 3 s con 1000 encuentros pendientes | TD-09 |
| LOW | Idioma y observabilidad | La razón de C14 en inglés en el portal docente; el commit por turno. Los avisos en inglés (TD-23) se corrigieron en el ciclo 8 | TD-07, TD-10 |

## Qué cambió desde el ciclo 6

| En el ciclo 6 | Ahora |
|---|---|
| **BLOCKER:** pérdidas sin aviso de hemoderivados | **Corregidas por clase** (C-2026-09-28-13). También las medidas de hemorragia, la IO y la prueba de embarazo (C-2026-09-28-14) |
| **BLOCKER:** sobrecarga falsa en trauma | **Corregida** (C-2026-09-28-12) |
| HIGH: C4 valorable | **C4 = NO** (C-2026-09-28-10); C14: 14 YES, 17 NO y 0 sin revisar (C-2026-09-28-11) |
| HIGH: PostgreSQL no probado | **Verificado** en local (TD-24 cerrado) |
| MEDIUM: I-F02, L-F02 y L-F07 | **Corregidos** (C-2026-09-28-15 y 16) |

## Lo que este documento no afirma

- **No afirma una evaluación validada.** Tampoco que el simulador pruebe
  competencia, prediga el desempeño clínico o sea comparable entre programas.
- **No reemplaza al piloto de validación.** La primera medición humana se hace
  contra el SPANISH PILOT BASELINE.
- **La regla cuando lleguen datos humanos es MEASURE FIRST:** BASELINE →
  MEASUREMENT → ANNOTATION → ADJUDICATION → ERROR CLASSIFICATION →
  PRIORITIZATION → APPROVED FIX.
