# Registro de deuda técnica

Ciclo 5 del AI Advisor (59BQ), 2026-09-28, con la extensión nocturna.

**Qué es:** la consolidación de lo registrado en defectos conocidos (KD), el
Decision File (DF), las auditorías y las limitaciones conocidas, para que nada
importante se pierda entre documentos.

**Qué no hay:** deuda inventada. Cada fila cita dónde está la evidencia.

**Leyenda de «¿Bloquea el piloto?»:** el piloto de validación v1 (seis
casos, documentos en español, sin C14 ni SCA). Mide el lector: no lo bloquea
un defecto que el piloto puede medir.

## CRITICAL

| ID | Área | Descripción | Impacto en el usuario | Evidencia | Conocido desde | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|---|---|
| TD-12 | Lector | 9 clases de oración pierden una orden de primera línea o la archivan como plan: «Dx: orden», «X, si no responde, Y», «Ahora X y luego repetir», «Por … instalo …», «cambia a Ringer», destino «con/on» tratamiento, «Activo hemodinamia», TXA «en 10 min», un hallazgo tras la orden | El encuentro no hace lo que se escribió, y el Trace atribuye la omisión al residente | `AUDITORIA_TRACE_CICLO5.md` (C01–C09); 3 reproducidas por la sesión principal | ciclo 5 (auditoría nocturna); presentes desde antes del baseline español | No: el piloto las mide (59I) | Tras el piloto, con `PRIORIZACION_POST_PILOTO.md` (DF-22) |
| TD-13 | Página | «Urgent intervention executed» cuando nada corrió, con oferta de explicarla después; preguntas atadas a órdenes mal leídas | La página afirma una decisión que no ocurrió; contestar puede ejecutar lo equivocado | `AUDITORIA_TRACE_CICLO5.md` (59O-03, 59O-06) | ciclo 5 | No | 59O-03 antes de un piloto con residentes (DF-22) |

## HIGH

| ID | Área | Descripción | Impacto en el usuario | Evidencia | Conocido desde | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|---|---|
| TD-01 | Caso clínico | `acs_54m_inferior`: el caso y el motor tienen VD comprometido; el POCUS dice VD normal | El residente ve datos que se contradicen; si confía en el POCUS y da nitratos, la fisiología lo castiga | `AUDITORIA_ACS_54M_INFERIOR.md` | ciclo 4 (borrador C14) | No | Tras la decisión docente (DF-20) |
| TD-14 | Lector | 14 clases HIGH de la auditoría del Trace (conectores, adverbio inicial, «2 U de GR», pruebas cruzadas, estudios con conteo, «más/plus», volúmenes coloquiales, marcapaso sin verbo, insulina con SG, suspender heparina, entre otras) | Órdenes frecuentes retenidas o perdidas | `AUDITORIA_TRACE_CICLO5.md` (H01–H14) | ciclo 5 | No: el piloto las mide | Tras el piloto (DF-22) |

## MEDIUM

| ID | Área | Descripción | Impacto en el usuario | Evidencia | Conocido desde | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|---|---|
| KD-02 | Lector | Fármaco sin verbo ni dosis no es orden; en una lista se pierde sin aviso | Orden perdida en silencio | `KNOWN_DEFECTS.md` | ciclo 4 | No (medir) | Decisión docente: ¿preguntar la dosis? |
| KD-03 | Lector / interacción | Texto escrito con una aclaración pendiente se toma como su respuesta | Una orden nueva puede leerse como respuesta | ídem | ciclo 4 | No (la herramienta cancela) | Fase 2 |
| KD-05 | Lector | «OK to discharge…» no se lee como alta | Alta perdida en inglés | ídem | ciclo 4 | No (fase EN) | Con las altas en inglés |
| KD-06 | Lector | La receta unida al alta con «con/with» se pierde | Receta perdida | ídem | ciclo 3 | Posible en C05 | Guardar la receta como receta |
| KD-11 | Trace | Una indicación de vigilancia queda como modelo de trabajo | Cita no fiel | ídem | ciclo 4 | No | Familia DF-7 |
| KD-15 | Lector | Fluido nombrado en palabras sin verbo («IV fluids 1 L») no es orden | Envío retenido | ídem | ciclo 5 | No (fase EN) | Clase de nombres de fluido, con decisión docente |
| TD-02 | Evidencia | No existe «oportunidad ofrecida pero no demostrada»: se confunde con pendiente o con desempeño insuficiente | Lectura injusta del progreso | auditoría nocturna, anexo 59AJ | ciclo 5 | No | DF-17, tras el piloto C14 |
| TD-03 | Procedencia | Los vínculos de marco de los 8 Decision Challenges no se congelan con la observación, sólo la versión del mapping | Una exportación por hito leería los vínculos actuales | auditoría nocturna, anexo 59BG | ciclo 5 | No | Antes de cualquier exportación por marco |
| TD-04 | Datos clínicos | Todo el POCUS del banco sigue marcado como borrador (`POCUS_DRAFT_PENDING_FACULTY_REVIEW = True`) | C14 declara oportunidades sobre hallazgos de POCUS que el código aún llama borrador | `clinical_cases.py:64` | antes del ciclo 1 | No | Que el docente confirme el POCUS de los casos C14 YES (DF-23) |
| TD-05 | Pruebas | `test_generation_reload.py` muta módulos globales al importarse | Posible contaminación entre pruebas si el `reload` falla | auditoría nocturna, anexo 59R | ciclo 5 | No | Cuando se toque ese archivo |
| TD-06 | Documentación | `corrections_registry` no registra DF-7, DF-10 ni DF-16a/b/c de los ciclos 2–4, aunque dice registrar toda corrección | Trazabilidad incompleta | `grep` en el registro | ciclo 5 | No | Próximo ciclo con cambios de código |
| TD-08 | Datos clínicos | **Las 4 oclusiones coronarias:** el primer POCUS repetido baja la severidad redactada a «mildly reduced» con la arteria cerrada. De Winter (C14 YES): «Akinesis» → «mildly reduced» a los 30 min → «akinetic» a los 100 | Una mejoría aparente sin reperfusión | auditoría nocturna, sección 9; verificado en el motor | ciclo 5 (`acs_54m_inferior`), generalizado en la noche | No (sin SCA) | DF-23, junto con DF-20 |
| TD-09 | Desempeño | La cola docente resuelve la elegibilidad objetivo por objetivo, verificando otra vez la huella 17 veces por encuentro: 3,2 s con 1000 encuentros pendientes y 14,5 s con 5000 | Página docente lenta con cohortes grandes | auditoría nocturna, sección 3 (perfilado) | ciclo 5 | No | Antes de cohortes de más de ~20 residentes (DF-24) |
| TD-15 | Integridad longitudinal | Los temas de historia se leen del banco vivo, no del caso congelado: un cambio del banco reinterpreta encuentros antiguos, también un tamizaje de evento crítico | Informes de encuentros antiguos que cambian | `history_review.py:126-133` (L-F01) | ciclo 5 | No | DF-24 |
| TD-16 | Perfil | El perfil ordena por fecha de confirmación, no del encuentro | «Último» y «cambio» pueden contradecir la trayectoria | `rubric_portal.py:485-487` (L-F04) | ciclo 5 | No | DF-24 |

## LOW

| ID | Área | Descripción | Evidencia | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|
| KD-04, KD-07, KD-08, KD-09, KD-10, KD-12, KD-13, KD-14 | Lector / Trace | Los residuos LOW de DF-16 y DF-11 | `KNOWN_DEFECTS.md` | No | Según el piloto |
| TD-07 | Idioma | La razón y la evidencia esperada de C14 se muestran en inglés en el portal docente en español | auditoría nocturna, sección 5 | No | Con revisión docente de la traducción |
| TD-10 | Observabilidad | El Trace no guarda el commit por turno, sólo al iniciar el encuentro | auditoría nocturna, anexo 59AP | No | Campo corto, cuando se toque el Trace |
| TD-11 | Lenguaje de docs | «validated trajectory» significa «probada», no validación clínica | README | No | En textos nuevos |
| TD-17 | Exportación y perfil | La exportación del residente trae `reviewed_by` vacío; el perfil elige la «última» rúbrica por hora y no por número de revisión | `rubric_store.py:417-432` (I-F02, L-F02) | No | DF-24 |
| TD-18 | Integridad | Migración: la foto de una confirmación absorbe observaciones posteriores (I-F18); directiva y encuentro en dos transacciones (I-F09); `sequence` sin restricción única (I-F06); duplicados previos o un JSON corrupto tiran la vista (I-F19/20); errores sin registro (I-F10) | auditoría nocturna, sección 1 | No | DF-24 |
| TD-19 | Clínica menor | `bradycardia_bb_54f` somnolienta pero «Alert» en el monitor; FA con ritmo sinusal en 2 casos; embarazo no redactado | auditoría nocturna, sección 9 | No | DF-23 |

## Corregido en la extensión nocturna

- **59Z · un encuentro nuevo heredaba el cierre del anterior**
  (C-2026-09-28-03).
  - El aviso de cierre abría el encuentro siguiente.
  - El registro de cierre se guardaba en él.
  - Corregido en `reset_session()`, con 3 pruebas en la página real.

## Conducta por diseño (no es deuda)

- **KB-01:** el oxígeno sin flujo absoluto se retiene para preguntar el flujo.
- **KB-02:** un «IN» suelto antes del fármaco no se lee como vía nasal.
- **Reenviar una orden es un turno nuevo.** Si el motor la repite depende del
  fármaco: una dosis única ya dada no se repite.
