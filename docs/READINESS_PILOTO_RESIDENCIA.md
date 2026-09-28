# Readiness del piloto con residentes (ciclo 6)

Instrucción docente del 2026-09-28, ciclo 6 (§54, §87 y §88). Actualiza la
lista «¿Qué impediría hoy un piloto real de residencia?» de la auditoría
nocturna del ciclo 5 (`AUDITORIA_NOCTURNA_CICLO5.md`, sección 13), después de
DF-22 y 59O-03.

**Esto es readiness técnica, no validez metodológica.**

- Lo implementado no está validado (CURRENTLY IMPLEMENTED ≠ VALIDATED).
- El sistema puede estar técnicamente listo para pilotear sin estar validado
  como instrumento de evaluación.
- Las cifras de los conjuntos ciegos son INTERNAL DEVELOPMENT DATA.

## Dos pilotos distintos

| | VALIDATION PILOT | REAL RESIDENCY PILOT |
|---|---|---|
| Qué es | Médicos que escriben offline, en Word, para evaluar el motor | Residentes que usan el simulador |
| Qué mide | Si el motor entiende, ejecuta y registra lo que un médico escribió | El uso real: flujo, fricción, carga docente. No mide validez |
| Estado | **PILOT TOOLING READY** desde el ciclo 5 (`validation/pilot_v1/READINESS.md`). Puede empezar antes | **WITH CONDITIONS** (abajo) |
| Contra qué commit | SPANISH PILOT BASELINE `939978a`, inmutable | DEVELOPMENT HARDENED BASELINE V1 (`validation/BASELINES.md`) |
| Qué falta | Lo del docente: revisar los 18 documentos, reclutar y enviar | Las condiciones de abajo |

El piloto con residentes pide más seguridad de ejecución y de Trace que el de
validación: un residente ve la simulación responder a lo que el motor ejecutó.

## TECHNICALLY READY FOR CONTROLLED PILOT?

**WITH CONDITIONS.**

1. **Uso formativo.**
   - Ninguna decisión evaluativa sale del Trace solo.
   - Cada rúbrica la confirma un docente.
   - Esto vale hasta que el piloto de validación mida el lector con texto
     externo (DF-15).
2. **Trauma.** Decidir TD-21 (sobrecarga transfusional con hemorragia
   activa), o dejar fuera los dos casos de trauma.
3. **Hemoderivados.** Corregir por clase las pérdidas sin aviso de TD-26
   («2 U de GR O negativo», el protocolo de transfusión masiva), con su
   aprobación. Mientras tanto, dejar fuera los casos que piden transfundir.
4. **C4.** Escribir C4 = NO en el banco (decidido en TDFC-7) antes de que los
   encuentros de residentes generen evidencia. Hoy la transición lo deja
   valorable en todo encuentro.
5. **PostgreSQL.** Verificar en la base de staging que el perfil (L-F04) y la
   historia de un encuentro (L-F01) se leen igual que en SQLite (TD-24).

## ¿Qué impediría hoy un piloto real con residentes?

| Clase | Área | Qué | Referencia |
|---|---|---|---|
| **BLOCKER** | Fidelidad del Trace | Quedan pérdidas sin aviso, sobre todo de hemoderivados: la orden no corre, nada lo dice y el Trace muestra al residente sin hacerla. Con el código final: 5 de 108 y 4 de 32 positivas ciegas | TD-26 · condición 3 |
| **BLOCKER** | Consistencia clínica | Transfundir una hemorragia activa dispara la sobrecarga transfusional | TD-21 · condición 2 |
| **BLOCKER** para un uso evaluativo | Estado de validación | La fidelidad del lector con texto externo no está medida | DF-15 · condición 1 |
| HIGH | Evidencia | C4 sigue valorable por la transición, aunque C4 = NO está decidido | DF-21 · condición 4 |
| HIGH | Infraestructura | PostgreSQL no se probó en el ciclo 6 | TD-24 · condición 5 |
| HIGH | Fricción del lector | Mucho de lo escrito se retiene con una pregunta: 63 de 108 positivas ciegas. Es honesto, pero cuesta turnos | TD-14 · medir en el piloto |
| HIGH | Flujo docente | Con la transición, cada encuentro deja 6 a 8 objetivos por valorar | DF-12, DF-21 |
| MEDIUM | Integridad longitudinal | I-F02, L-F02, I-F18 y L-F07 | DF-24, en una línea |
| MEDIUM | Consistencia clínica | Las filas 3 a 11 de DF-23; `acs_54m_inferior` sigue NOT REVIEWED | CLINICAL REVIEW |
| MEDIUM | Escala | La cola docente es lineal: 3 s con 1000 encuentros pendientes | TD-09 |
| MEDIUM | Privacidad | `get_progress` con token de residente trae la evidencia esperada del caso (no se muestra) | I-F25 |
| LOW | Idioma | Avisos que quedan en inglés en la interfaz en español | TD-23 |
| LOW | Observabilidad y pruebas | El commit por turno; un nombre de prueba engañoso | TD-10, TD-25 |

## Qué cambió desde el ciclo 5

| En el ciclo 5 | Ahora |
|---|---|
| **BLOCKER:** las clases CRITICAL del lector | **Corregidas por clase** (DF-22, C-2026-09-28-04). Lo que midieron los conjuntos ciegos queda en TD-26 (BLOCKER) y TD-14 (HIGH) |
| HIGH: «Urgent intervention executed» cuando nada corrió (59O-03) | **Corregido.** Casos A–F de punta a punta, EN/ES (C-2026-09-28-05) |
| HIGH: preguntas atadas a órdenes mal leídas (59O-06) | **En parte.** El hallazgo tras una orden ya no crea una orden fantasma (C09). Queda la tasa de SG ante una insulina (H11) |
| — | **Nuevo, corregido:** lo que hizo el equipo prehospitalario ya no corre como orden del residente; un suero escrito con su vía («por VVP») ya no se pierde |
| HIGH: `acs_54m_inferior` y el POCUS de las oclusiones | De Winter corregido (C-2026-09-28-08). `acs_54m_inferior` sin cambio, NOT REVIEWED |
| MEDIUM: temas de historia vivos (L-F01) y cronología del perfil (L-F04) | **Corregidos** (C-2026-09-28-06 y 07) |

## Lo que este documento no afirma

- **No afirma una evaluación validada.** Tampoco que el simulador pruebe
  competencia, prediga el desempeño clínico o sea comparable entre programas.
  Son objetivos de investigación, no hechos actuales.
- **No reemplaza al piloto de validación.** La primera medición humana se hace
  contra el SPANISH PILOT BASELINE.
- **La regla cuando lleguen datos humanos (§89) es MEASURE FIRST:** BASELINE →
  MEASUREMENT → ANNOTATION → ADJUDICATION → ERROR CLASSIFICATION →
  PRIORITIZATION → APPROVED FIX.
