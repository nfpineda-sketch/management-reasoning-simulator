# Registro de deuda técnica

Ciclo 5 del AI Advisor (59BQ), 2026-09-28, con la extensión nocturna.
**Actualizado al cierre del ciclo 6** (2026-09-28): lo corregido pasa a
«Corregido en el ciclo 6», con su registro; lo nuevo lleva su evidencia.

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

## HIGH

| ID | Área | Descripción | Impacto en el usuario | Evidencia | Conocido desde | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|---|---|
| TD-01 | Caso clínico | `acs_54m_inferior`: el caso y el motor tienen VD comprometido; el POCUS dice VD normal | El residente ve datos que se contradicen; si confía en el POCUS y da nitratos, la fisiología lo castiga | `AUDITORIA_ACS_54M_INFERIOR.md` | ciclo 4 (borrador C14) | No | Tras la decisión docente (DF-20) |
| TD-21 | Motor · trauma | Transfundir un shock hemorrágico traumático dispara la sobrecarga transfusional («the haemoglobin was already adequate»): la familia trauma no baja la hemoglobina con la pérdida y la regla mira Hb ≥ 10 | Enseña que la sangre daña en los dos casos de trauma, ambos C14 YES | `docs/AUDITORIA_DF23_CICLO6.md` §7.1; reproducido por la sesión principal en `trauma_limb_hemorrhage_27m` | ciclo 6 | No para el piloto de validación; **sí para uno con residentes** | Decisión docente: excluir la hemorragia activa de la regla (recomendado) o bajar la Hb con la pérdida |
| TD-22 | Lector | Una prueba de embarazo (β-hCG, test de embarazo) no se reconoce y retiene todo el envío, también la angio-TC | En `pulmonary_embolism_33f` la conducta prudente retiene la tanda | `docs/AUDITORIA_DF23_CICLO6.md` §4.3 | ciclo 6 | No | Registrarla como estudio «no modelado» (cumple las seis condiciones; no se aplicó por la regla §64) |
| TD-14 | Lector | **Lo que queda tras DF-22, medido por los tres conjuntos ciegos del ciclo 6.** Vocabulario: «amp of D50», nitroglicerina SL o en infusión, heparina e insulina por kilo, «epi drip», «Narcan», «Page GI», «STEMI code», destinos (floor, OR, pabellón), fluidos (D5W, glucosalino, cristaloides), «run/hang/push», «5.000». Formas: una condición escrita como rótulo sin «si» (el rótulo ya no se salta, pero lo que sigue corre ahora); una retención después del fármaco («y alteplase tampoco por ahora»); una receta en lista tras el alta (KD-06); lo que hizo el equipo prehospitalario seguido de coma, o un pensamiento seguido de «y» («pensando en dar X y poner Y»); insulina con SG (H11); y las 14 clases HIGH de la auditoría del ciclo 5 (H01–H14) | En el motor, la mayoría se retiene con una pregunta (63 de 108 y 19 de 32 en los conjuntos ciegos); las tres lecturas falsas medidas quedaron retenidas | `MEDICION_RECONOCIMIENTO_ORDENES.md` (ciclo 6); `AUDITORIA_TRACE_CICLO5.md` (H01–H14) | ciclo 5 | No: el piloto las mide | Tras el piloto de validación, priorizadas por su medición |
| TD-26 | Lector | **Pérdidas sin aviso que quedan, sobre todo hemoderivados:** «2 U de GR O negativo», «O-neg», el protocolo de transfusión masiva, «2 large-bore IVs» con el suero en la misma frase. La orden no corre, nada lo dice, y el Trace muestra al residente sin hacerla | Omisión atribuida al residente en trauma y HDA | conjuntos ciegos del ciclo 6: 5 de 108 y 4 de 32 positivas perdidas sin aviso en el motor | ciclo 6 | No para el piloto de validación (lo mide); **sí para uno con residentes** | Corrección por clase de hemoderivados, con aprobación docente, antes de un piloto con residentes |

## MEDIUM

| ID | Área | Descripción | Impacto en el usuario | Evidencia | Conocido desde | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|---|---|
| KD-02 | Lector | Fármaco sin verbo ni dosis no es orden; en una lista se pierde sin aviso | Orden perdida en silencio | `KNOWN_DEFECTS.md` | ciclo 4 | No (medir) | Decisión docente: ¿preguntar la dosis? |
| KD-03 | Lector / interacción | Texto escrito con una aclaración pendiente se toma como su respuesta | Una orden nueva puede leerse como respuesta | ídem | ciclo 4 | No (la herramienta cancela) | Fase 2 |
| KD-05 | Lector | «OK to discharge…» no se lee como alta | Alta perdida en inglés | ídem | ciclo 4 | No (fase EN) | Con las altas en inglés |
| KD-11 | Trace | Una indicación de vigilancia queda como modelo de trabajo | Cita no fiel | ídem | ciclo 4 | No | Familia DF-7 |
| KD-15 | Lector | Fluido nombrado en palabras sin verbo («IV fluids 1 L») no es orden | Envío retenido | ídem | ciclo 5 | No (fase EN) | Clase de nombres de fluido, con decisión docente |
| TD-02 | Evidencia | No existe «oportunidad ofrecida pero no demostrada»: se confunde con pendiente o con desempeño insuficiente | Lectura injusta del progreso | auditoría nocturna, anexo 59AJ | ciclo 5 | No | DF-17, tras el piloto C14 |
| TD-03 | Procedencia | Los vínculos de marco de los 8 Decision Challenges no se congelan con la observación, sólo la versión del mapping | Una exportación por hito leería los vínculos actuales | auditoría nocturna, anexo 59BG | ciclo 5 | No | Antes de cualquier exportación por marco |
| TD-04 | Datos clínicos | Todo el POCUS del banco sigue marcado como borrador (`POCUS_DRAFT_PENDING_FACULTY_REVIEW = True`) | C14 declara oportunidades sobre hallazgos de POCUS que el código aún llama borrador | `clinical_cases.py:64` | antes del ciclo 1 | No | Que el docente confirme el POCUS de los casos C14 YES (DF-23) |
| TD-05 | Pruebas | `test_generation_reload.py` muta módulos globales al importarse | Posible contaminación entre pruebas si el `reload` falla | auditoría nocturna, anexo 59R | ciclo 5 | No | Cuando se toque ese archivo |
| TD-06 | Documentación | `corrections_registry` no registra DF-7, DF-10 ni DF-16a/b/c de los ciclos 2–4, aunque dice registrar toda corrección | Trazabilidad incompleta | `grep` en el registro | ciclo 5 | No | Próximo ciclo con cambios de código |
| TD-08 | Datos clínicos | **Oclusiones coronarias, lo que queda tras el ciclo 6.** De Winter se corrigió (C-2026-09-28-08). Quedan ambiguos: el grado de «reduced» en `acs_70f_left_main` y `acs_54m_inferior`; el pulmón por defecto «No B-lines» del tronco frente a crepitantes y congestión; y la pared que vuelve a «contract normally» a las 2–3 h de reperfundir mientras el evento dice «recovers only partly» | Textos que no dicen lo mismo que el resto del caso | `docs/AUDITORIA_DF23_CICLO6.md` §1 y §5 | ciclo 5 | No (sin SCA) | Decisión docente (cola de decisiones, CLINICAL REVIEW) |
| TD-09 | Desempeño | La cola docente resuelve la elegibilidad objetivo por objetivo, verificando otra vez la huella 17 veces por encuentro: 3,2 s con 1000 encuentros pendientes y 14,5 s con 5000 | Página docente lenta con cohortes grandes | auditoría nocturna, sección 3 (perfilado) | ciclo 5 | No | Antes de cohortes de más de ~20 residentes (DF-24) |

## LOW

| ID | Área | Descripción | Evidencia | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|
| KD-04, KD-07, KD-08, KD-09, KD-10, KD-12, KD-13, KD-14 | Lector / Trace | Los residuos LOW de DF-16 y DF-11 | `KNOWN_DEFECTS.md` | No | Según el piloto |
| TD-07 | Idioma | La razón y la evidencia esperada de C14 se muestran en inglés en el portal docente en español | auditoría nocturna, sección 5 | No | Con revisión docente de la traducción |
| TD-10 | Observabilidad | El Trace no guarda el commit por turno, sólo al iniciar el encuentro | auditoría nocturna, anexo 59AP | No | Campo corto, cuando se toque el Trace |
| TD-11 | Lenguaje de docs | «validated trajectory» significa «probada», no validación clínica | README | No | En textos nuevos |
| TD-17 | Exportación y perfil | La exportación del residente trae `reviewed_by` vacío; el perfil elige la «última» rúbrica por hora y no por número de revisión | `rubric_store.py:417-432` (I-F02, L-F02) | No | DF-24 |
| TD-18 | Integridad | Migración: la foto de una confirmación absorbe observaciones posteriores (I-F18); directiva y encuentro en dos transacciones (I-F09); `sequence` sin restricción única (I-F06); duplicados previos o un JSON corrupto tiran la vista (I-F19/20); errores sin registro (I-F10) | auditoría nocturna, sección 1 | No | DF-24 |
| TD-23 | Idioma | En español quedan en inglés el aviso «Urgent intervention executed…», el de la anulación docente y las frases del modelo del POCUS («mildly reduced contraction») | ciclo 6 (59O-03, DF-23 §7.2) | No | Con la próxima revisión de la traducción |
| TD-24 | Infraestructura | PostgreSQL no se probó en el ciclo 6: el servidor local no puede usar el directorio privado de la sesión. La única consulta SQL que cambió (L-F04) es un alias de columna estándar, probada en SQLite | ciclo 6 | No | Verificar el perfil en la base de staging antes de un piloto con residentes |
| TD-25 | Pruebas | `test_acs_reperfusion.py` llama a una prueba «reperfusion prevents the block and the arrest» y el bloqueo ocurre en su propio escenario; sólo comprueba la FV | agente DF-24/TDFC, ciclo 6 | No | Renombrar cuando se toque el archivo |
| TD-19 | Clínica menor | `bradycardia_bb_54f` corregida (llega somnolienta, C-2026-09-28-08). Quedan: `anaphylaxis_63m_betablocked` con pulso irregular y monitor sinusal (dos arreglos posibles); embarazo no redactado en 4 mujeres, y la pregunta por la última regla responde con el inicio de los síntomas | `docs/AUDITORIA_DF23_CICLO6.md` §2–§4 | No | Decisión docente |

## Corregido en el ciclo 6

| ID | Qué | Registro |
|---|---|---|
| TD-12 | Las nueve clases CRITICAL del lector (C01–C09), por clase. Después de medir, lo que hallaron los conjuntos ciegos en las correcciones mismas: el ácido tranexámico en una historia; lo unido con «y/and» a lo que hizo el equipo prehospitalario (se pregunta); un rótulo con umbral, estado o resultado; y la vía por la que pasa un suero («SF 500 mL por VVP», «via the PIV»), que perdía el bolo e instalaba una vía. Los residuos están en TD-14, TD-26 y `MEDICION_RECONOCIMIENTO_ORDENES.md` | C-2026-09-28-04 |
| KD-06 | La receta unida al alta con «con/with» queda como receta, nunca como dosis dada | C-2026-09-28-04 (clase C05) |
| 59O-06 (parte) | La pregunta por una orden fantasma: un hallazgo tras la orden («satura 86 % con la naricera») ya no es una segunda orden (C09). La vía ya escrita se había corregido en el ciclo 5 (KD-01). Queda la tasa de SG que se pregunta ante una insulina (H11, en TD-14) | C-2026-09-28-04 (clase C09) |
| TD-13 | «Urgent intervention executed» y la oferta de explicarla salen sólo de una ejecución real; «no sé» ante una orden retenida ya no la hace desaparecer | C-2026-09-28-05 |
| TD-15 | Los temas de historia se leen del caso congelado del encuentro (L-F01) | C-2026-09-28-06 |
| TD-16 | El perfil se ordena por la fecha del encuentro (L-F04) | C-2026-09-28-07 |
| TD-08 (parte) · TD-19 (parte) | De Winter conserva la acinesia con la arteria cerrada; `bradycardia_bb_54f` llega somnolienta | C-2026-09-28-08 |

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
