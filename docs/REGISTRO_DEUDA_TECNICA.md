# Registro de deuda técnica

Ciclo 5 del AI Advisor (59BQ), 2026-09-28, con la extensión nocturna.
**Actualizado al cierre del ciclo 7** (2026-09-28): lo corregido pasa a
«Corregido en el ciclo 7», con su registro; lo nuevo (TD-29 a TD-32) lleva su
evidencia. El cierre del ciclo 6 sigue más abajo.

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
| TD-01 | Caso clínico | `acs_54m_inferior`: el caso y el motor tienen VD comprometido; el POCUS dice VD normal. **Ciclo 7:** su C14 es NO (C-2026-09-28-11), por la oportunidad de observación; **la contradicción de datos sigue** | El residente ve datos que se contradicen; si confía en el POCUS y da nitratos, la fisiología lo castiga | `AUDITORIA_ACS_54M_INFERIOR.md` | ciclo 4 (borrador C14) | No (sin SCA) | DF-20 A/B/C/D: NEEDS NICOLÁS |
| TD-33 | Motor · trauma | **Residuo de TD-21.** Con el sangrado controlado y la pérdida repuesta con cristaloide (torniquete + 3 L de SF), transfundir 2 U dispara la sobrecarga: la regla da la pérdida por repuesta con cristaloide y la familia trauma no diluye la Hb | Tras el error típico (cristaloide en vez de sangre), la sangre «hace daño»; no es un evento crítico ni toca el puntaje | `docs/TD21_SOBRECARGA_TRANSFUSIONAL.md`, residuo; sonda de rúbrica del ciclo 7 | ciclo 7 | No para el piloto de validación (sin trauma); para uno con residentes, avisar al docente o decidir | Decisión docente: que sólo la sangre reponga el déficit en esa regla (recomendado; una línea) |
| TD-29 | Lector | **«When», «cuando» y «once» no hacen condicional una orden que no es sangre:** «When BP drops, give NS 500 mL» y «Cuando baje la PA, bolo SF 500 mL» corren ahora; «if» y «si» sí la guardan como plan (DF-16b). En la sangre, «cuando» y «once» ya preguntan (TD-26). Igual antes del ciclo 7 | Una orden condicionada corre de inmediato, a la vista en la sala | revisión del ciclo 7; `docs/TD26_HEMODERIVADOS_Y_C7_06.md`, «Límites» | ciclo 7 (anterior al ciclo) | No para el piloto de validación (lo mide); no bloquea un piloto formativo, porque se ve en la sala | Ciclo 8: extender la condición de DF-16b a «when/cuando/once/en cuanto», con decisión sobre «cuando puedas» |
| TD-14 | Lector | **Lo que queda tras DF-22, medido por los tres conjuntos ciegos del ciclo 6.** Vocabulario: «amp of D50», nitroglicerina SL o en infusión, heparina e insulina por kilo, «epi drip», «Narcan», «Page GI», «STEMI code», destinos (floor, OR, pabellón), fluidos (D5W, glucosalino, cristaloides), «run/hang/push», «5.000». Formas: una condición escrita como rótulo sin «si» (el rótulo ya no se salta, pero lo que sigue corre ahora); una retención después del fármaco («y alteplase tampoco por ahora»); una receta en lista tras el alta (KD-06); lo que hizo el equipo prehospitalario seguido de coma, o un pensamiento seguido de «y» («pensando en dar X y poner Y»); insulina con SG (H11); y las 14 clases HIGH de la auditoría del ciclo 5 (H01–H14) | En el motor, la mayoría se retiene con una pregunta (63 de 108 y 19 de 32 en los conjuntos ciegos); las tres lecturas falsas medidas quedaron retenidas | `MEDICION_RECONOCIMIENTO_ORDENES.md` (ciclo 6); `AUDITORIA_TRACE_CICLO5.md` (H01–H14) | ciclo 5 | No: el piloto las mide | Tras el piloto de validación, priorizadas por su medición |

## MEDIUM

| ID | Área | Descripción | Impacto en el usuario | Evidencia | Conocido desde | ¿Bloquea el piloto? | Momento recomendado |
|---|---|---|---|---|---|---|---|
| KD-02 | Lector | Fármaco sin verbo ni dosis no es orden; en una lista se pierde sin aviso | Orden perdida en silencio | `KNOWN_DEFECTS.md` | ciclo 4 | No (medir) | Decisión docente: ¿preguntar la dosis? |
| KD-03 | Lector / interacción | Texto escrito con una aclaración pendiente se toma como su respuesta | Una orden nueva puede leerse como respuesta | ídem | ciclo 4 | No (la herramienta cancela) | Fase 2 |
| KD-05 | Lector | «OK to discharge…» no se lee como alta | Alta perdida en inglés | ídem | ciclo 4 | No (fase EN) | Con las altas en inglés |
| KD-11 | Trace | Una indicación de vigilancia queda como modelo de trabajo | Cita no fiel | ídem | ciclo 4 | No | Familia DF-7 |
| KD-15 | Lector | Fluido nombrado en palabras sin verbo («IV fluids 1 L») no es orden | Envío retenido | ídem | ciclo 5 | No (fase EN) | Clase de nombres de fluido, con decisión docente |
| TD-30 | Lector | **Órdenes sin verbo que siguen sin leerse, como antes del ciclo 7 (clase KD-02):** «surgery consult», «Endoscopía urgente» (también «para control de hemorragia»), «2 large-bore IVs» y «2 large-bore IVs or IO», hemocultivos sin verbo; un verbo desconocido sin cantidad junto a otras órdenes. Antes, «Endoscopía urgente para control de hemorragia» y «Hemorrhage control: surgery consult» aplicaban presión directa; ya no | Orden perdida sin aviso | revisión adversarial del ciclo 7 (T42, T46) | ciclo 7 | No (medir) | Con KD-02 y TD-14 |
| TD-31 | Motor · lector | **Preguntas y sumas que no corresponden:** la adrenalina IM sin dosis pregunta una velocidad en mcg/min; «Direct pressure with packing» son dos medidas y el motor suma su efecto, que controla el sangrado como un torniquete (regla de medidas combinadas, sin cambio) | Una pregunta en otra unidad; un control algo mayor que el de cada medida | revisión del ciclo 7 (T37) | ciclo 7 (anterior al ciclo) | No | Con la revisión de la regla de medidas combinadas |
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
| TD-18 | Integridad | Migración: la foto de una confirmación absorbe observaciones posteriores (I-F18); directiva y encuentro en dos transacciones (I-F09); `sequence` sin restricción única (I-F06); duplicados previos o un JSON corrupto tiran la vista (I-F19/20); errores sin registro (I-F10) | auditoría nocturna, sección 1 | No | DF-24 dejó fuera I-F18 (ciclo 7); el resto, sin decisión |
| TD-23 | Idioma | En español quedan en inglés el aviso «Urgent intervention executed…», el de la anulación docente y las frases del modelo del POCUS («mildly reduced contraction») | ciclo 6 (59O-03, DF-23 §7.2) | No | Con la próxima revisión de la traducción |
| TD-25 | Pruebas | `test_acs_reperfusion.py` llama a una prueba «reperfusion prevents the block and the arrest» y el bloqueo ocurre en su propio escenario; sólo comprueba la FV | agente DF-24/TDFC, ciclo 6 | No | Renombrar cuando se toque el archivo |
| TD-27 | Desempeño | Una racha de ~2000 espacios seguidos tarda ~1 s en leerse; ya era así en el ciclo 5 (`_sequenced` y la intención declarada). La racha que el ciclo 6 hacía cúbica está corregida | revisión adversarial del ciclo 6 | No | Colapsar espacios al normalizar, cuando se toque el lector |
| TD-28 | Lector | Una pregunta cita el texto normalizado, no el escrito («administrar tranexamico» por «pasó tranexámico»); ya era así antes del ciclo | revisión adversarial del ciclo 6 | No | Citar el texto original del residente |
| TD-32 | Lector | **Residuos LOW de TD-26, sin aviso:** «Deactivate MTP», «Platelets if count < 50», «2 U. GR» (el punto parte la frase), el «c/u» de una duración («2 U GR en 2 horas c/u» corre en 2 horas en total), y un estado de las pruebas cruzadas («en curso», «pending») registrado como pedido. Todo igual antes del ciclo | revisión adversarial y barrido final del ciclo 7 | No | Según el piloto |
| TD-19 | Clínica menor | `bradycardia_bb_54f` corregida (llega somnolienta, C-2026-09-28-08). Quedan: `anaphylaxis_63m_betablocked` con pulso irregular y monitor sinusal (dos arreglos posibles); embarazo no redactado en 4 mujeres, y la pregunta por la última regla responde con el inicio de los síntomas | `docs/AUDITORIA_DF23_CICLO6.md` §2–§4 | No | Decisión docente |

## Corregido en el ciclo 7

| ID | Qué | Registro |
|---|---|---|
| TD-21 | Transfundir una hemorragia activa en trauma ya no dispara una sobrecarga falsa (principio D); con el sangrado controlado y la pérdida repuesta, la regla vuelve. La HDA no cambia | C-2026-09-28-12 |
| TD-26 | Hemoderivados por clase, estándar A–J: glóbulos rojos en las unidades escritas; plasma, plaquetas, crioprecipitado y sangre total registrados como indicados, con su efecto no modelado; la activación del protocolo de transfusión masiva registrada, sin inventar nada; lo ambiguo, preguntado; nada que no sea una orden ahora transfunde. Residuos en TD-29, TD-30 y TD-32 | C-2026-09-28-13 |
| TD-22 | La prueba de embarazo se registra como pedida, sin resultado inventado, y no retiene nada | C-2026-09-28-14 |
| — | Control de hemorragia por medida y acceso intraóseo como tal (C7-06), EN/ES | C-2026-09-28-14 |
| DF-21 · C4 | C4 = NO en todo el entorno de observación | C-2026-09-28-10 |
| — | C14 NO en `acs_54m_inferior`: 31/31 casos revisados | C-2026-09-28-11 |
| TD-17 | La exportación dice quién confirmó (I-F02); el radar toma la revisión confirmada de mayor número (L-F02) | C-2026-09-28-15 |
| L-F07 | Las 9 composiciones de hipoglicemia heredan el C14 NO de su caso de origen | C-2026-09-28-16 |
| TD-24 | **PostgreSQL verificado** en un clúster PostgreSQL 16 local y descartable, sin datos reales, sobre el candidato final: 168 pruebas de persistencia pasan (115 bases creadas en PostgreSQL); las 3 que leen el archivo SQLite directamente no aplican, y su equivalente se comprobó a mano (la migración conserva las filas). El clúster se borró. Staging no se tocó (§9) | ciclo 7, C7-05 |
| — | El catálogo de hipoglicemia publicado estaba desactualizado desde `1c4194b` (no nombraba C-2026-09-28-10); `1c4194b` y `c61daf6` se subieron con esa prueba fallando. Regenerado | ciclo 7 |

## Corregido en el ciclo 6

| ID | Qué | Registro |
|---|---|---|
| TD-12 | Las nueve clases CRITICAL del lector (C01–C09), por clase. Después de medir, lo que hallaron los conjuntos ciegos en las correcciones mismas: el ácido tranexámico en una historia; lo unido con «y/and» a lo que hizo el equipo prehospitalario (se pregunta); un rótulo con umbral, estado o resultado; y la vía por la que pasa un suero («SF 500 mL por VVP», «via the PIV»), que perdía el bolo e instalaba una vía. Los residuos están en TD-14, TD-26 y `MEDICION_RECONOCIMIENTO_ORDENES.md` | C-2026-09-28-04 |
| KD-06 | La receta unida al alta con «con/with» queda como receta, nunca como dosis dada | C-2026-09-28-04 (clase C05) |
| 59O-06 (parte) | La pregunta por una orden fantasma: un hallazgo tras la orden («satura 86 % con la naricera») ya no es una segunda orden (C09). La vía ya escrita se había corregido en el ciclo 5 (KD-01). Queda la tasa de SG que se pregunta ante una insulina (H11, en TD-14) | C-2026-09-28-04 (clase C09) |
| TD-13 | «Urgent intervention executed» y la oferta de explicarla salen sólo de una ejecución real; «no sé» ante una orden retenida ya no la hace desaparecer | C-2026-09-28-05 |
| TD-15 | Los temas de historia se leen del caso congelado del encuentro (L-F01) | C-2026-09-28-06 |
| TD-16 | El perfil se ordena por la fecha del encuentro (L-F04) | C-2026-09-28-07 |
| — | Las regresiones de las propias correcciones que halló la revisión adversarial del diff: el «stop» prestado a la orden siguiente («Hold NS, O2 4 L NC» retiraba el oxígeno), la primera persona que ejecutaba preguntas, la prueba de historia que silenciaba órdenes comunes, el relato prehospitalario, el «RR» del ventilador, la sedación con su procedimiento, lo «ready», el tiempo de C01 y de C07, la página que caía al suspender un suero con duración, L-F01 con casos que eligió el modelo y «no se administra…». Y uno anterior al ciclo: la activación de un servicio se prestaba a los fármacos siguientes | C-2026-09-28-09 |
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
- **KB-03 (ciclo 6):** tras lo que hizo el equipo prehospitalario, «y coloco…» o
  «y paso…» se pregunta: sin su tilde, el verbo es también el pasado del equipo
  («colocó», «pasó»). Una pregunta no pierde la orden.
- **Reenviar una orden es un turno nuevo.** Si el motor la repite depende del
  fármaco: una dosis única ya dada no se repite.
