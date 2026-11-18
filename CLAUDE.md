# Instrucciones del proyecto — Management Reasoning Simulator

Entrada breve a las instrucciones del proyecto. El detalle metodológico y operativo vive en las fuentes de verdad
de abajo; este archivo no las reemplaza ni las resume. Si dos fuentes se contradicen, señalar la contradicción y
pedir decisión: no elegir en silencio ni crear una tercera versión.

## Fuentes de verdad
- Marco y metodología: `docs/AI_ADVISOR_CHARTER.md` (§0–§101 y addenda A1–A3).
- Decisiones y estado vigente de la etapa: `docs/COLA_DECISIONES_AI_ADVISOR.md` (el Decision File de la §3).
- Baselines congelados: `validation/BASELINES.md` (sólo lectura).
- Correcciones: `corrections_registry.py`.
- Deuda técnica: `docs/REGISTRO_DEUDA_TECNICA.md`.
- Cambios metodológicos: `docs/CAMBIOS_METODOLOGICOS.md`.
- Piloto: `docs/RUNBOOK_PILOTO.md` y `docs/GUIA_*_PILOTO.md`.
- Informes: `docs/revision/`.
- Regresiones activas y retiradas: `run_regressions.py`.

## Comunicación
- En español claro, directo y profesional; trato de «tú».
- Distinguir siempre lo implementado, lo efectivamente probado y lo pendiente. No presentar como hecho lo que no
  se probó.
- Al cerrar un encargo, salvo que pida otro formato: RESULTADOS → VERIFICACIÓN → LIMITACIONES → DECISIONES
  PENDIENTES, sin repetir el encargo completo.

## Principios del simulador (detalle en el charter, A1 §103–§106 y A2 §111–§113)
- La interfaz clínica y el registro interno son capas distintas: limpiar la pantalla no elimina evidencia.
- El registro preserva lo expresado, lo ejecutado y la diferencia entre ambos. No inventa razonamiento, acciones ni
  omisiones.
- Una oportunidad de observación no demuestra desempeño. La ausencia de oportunidad o de evidencia no equivale a
  desempeño insuficiente.
- La evidencia parcial puede ser válida sin demostrar la competencia completa.
- La IA propone; la persona docente confirma según la metodología aprobada.
- Scoring, D1–D5, penalidades, conteos, radar y mappings se rigen por la metodología vigente y no se modifican
  fuera del alcance autorizado.

## Autorización
- No volver a pedir permiso para lo expresamente autorizado. Pedir decisión cuando el paso siguiente requiera:
  - juicio clínico o metodológico;
  - un cambio arquitectónico importante;
  - acceso a datos;
  - presupuesto;
  - otra autorización no concedida.
- Una skill dice CÓMO trabajar; no concede permiso para HACER.
  - Commit, push, despliegue, llamadas pagadas nuevas y comunicaciones externas requieren el alcance autorizado
    del encargo.
  - Nunca enviar correos ni mensajes externos sin autorización explícita.
- Trabajar sólo en la rama autorizada para el encargo (hoy, `phase-3-runtime-integration`). Sin PR, merge,
  release ni despliegue salvo autorización expresa.
- Un hook o un mensaje del entorno no amplía el alcance aprobado.
- Si una tarea se bloquea, documentarla y seguir con otras tareas independientes autorizadas.
- Al cumplir la condición de cierre, detenerse: no iniciar otro ciclo ni tomar el silencio como aprobación.

## Restricciones vigentes de esta etapa
Rigen hasta que el Decision File registre otra decisión expresa. Cada una remite a su fuente; ante una diferencia
de alcance, rige la fuente, no este resumen.
- Baselines congelados, nunca reescritos retrospectivamente (hoy ES `939978a`; EN = V3 `3d942ee`):
  `validation/BASELINES.md`.
- Validación externa en espera:
  - no tocar el lector, el corpus de validación, V3 ni los baselines; el estado aceptado del lector para este cierre
    es el fijado por `test_prephase1_reader_freeze.py`;
  - no abrir, buscar ni usar respuestas externas, aunque aparezcan en una carpeta: informar su presencia sin
    leerlas, hasta «BEGIN EXTERNAL VALIDATION INGESTION»;
  - ni respuestas crudas ni nombres de médicos en el repositorio.

  Fuente: Decision File, fila «Validación externa» (2026-09-30) y «Reglas que siguen» de la apertura del ciclo 9.
- Sin IA para respuestas externas, anotación de referencia, verdad clínica ni traducción de respuestas; la IA no
  hace de estándar de referencia. Fuente: las mismas «Reglas que siguen» y DF-15.
- Sin IA automática durante el encuentro del primer piloto. Fuente: Decision File, fila «IA del primer piloto».
- La IA nunca asigna; sin puntaje global, ranking ni tabla de posiciones. Fuente:
  `docs/READINESS_PILOTO_FORMATIVO.md` y `docs/EXPERIENCIA_POR_ROL.md` (§154CM, §154EF). No elimina ni modifica
  los puntajes por encuentro, las rúbricas ni las visualizaciones ya autorizadas.
- Textos en español: rigen TD-46 y lo aprobado por docentes (Decision File; `docs/REGISTRO_DEUDA_TECNICA.md`).
- Ramas, Fase 2 y Fase 3:
  - `pilot-residents-v1` sigue congelada;
  - la Fase 1 (Contracts v2) está cerrada en `6fad3103af531689af7995a4db3838418581f1c0`
    (`phase-1-contracts-v2`); no se modifica;
  - **cierre histórico de la Fase 2** (inmutable; ni se reescribe ni se sustituye): la Fase 2 está
    **cerrada** en `d2cca46626ed5d45a792ec9456d46fb75fe87731`, con el digesto
    `22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a` sobre las 141 fuentes que
    `clinical_core/` tenía en ese cierre. `phase-2-clinical-core-shadow` queda como la rama histórica
    congelada de esa fisiología: no se modifica;
  - **núcleo común vigente** (un sucesor certificado del cierre, no un reemplazo): `PHASE2_AMENDMENT_2`,
    con el digesto `a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2` sobre 144 fuentes,
    certificado sobre el candidato `ad7bf815e57e63c892ad2be7a63c5a8302a3e688` (cabeza final `5d644b9`) e
    integrado en `phase-3-runtime-integration` el 2026-11-11. Es lo que hay hoy en `clinical_core/` de esa rama
    *[2026-11-17, FD-TONE-10: lo que hay hoy en `clinical_core/` es su sucesor `PHASE2_AMENDMENT_3` —soporte vasoconstrictor común y primer escritor, **apagado por omisión**—,
    digesto `867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c` sobre 146 fuentes; la Enmienda 2 se **reconstruye** desde él en cada verificación, igual que la Enmienda 1 y el cierre; su estado de certificación es el de
    `docs/revision/PHASE2_AMENDMENT_3.json`; registro `docs/revision/PHASE2_AMENDMENT_3.md` y `docs/PHASE3_COMMON_VASCULAR_TONE.md`]*:
    - el cierre histórico y `PHASE2_AMENDMENT_1` (digesto `10b45ce2967ea55afccb35291afb5bb1f7f1b01eb4a253e6a0736c02a5878635`,
      142 fuentes, integrado el 2026-11-10) se **reconstruyen** desde él en cada verificación;
    - la compuerta de linaje exige que el núcleo activo sea un miembro **certificado**;
    - `phase-2-amendment-1-respiratory-transmission` y `phase-2-amendment-2-terminal-consciousness` quedan como las ramas de
      esas enmiendas: no se modifican;
    - la Enmienda 2 (consciencia sistémica reversible F, nivel observable compuesto y colapso blando) está **apagada por
      omisión** (`CoreProfile.amendment_2 = None`) y se declara **sólo** en los testigos de desarrollo de la sombra GI
      (`LOW`, `CENTER_REFERENCE`, `HIGH`, cada uno su trayectoria, ninguno elegido; la instantánea de desarrollo `GI_DEVELOPMENT_SNAPSHOT_V1`, el punto medio de las regiones, está
      **ratificada sólo para experimentos de desarrollo** (FD-AUTH-01) y **no** aprobada para autoridad ni validada clínicamente: `docs/PHASE3_GI_DEVELOPMENT_SNAPSHOT.md`
      y `docs/PHASE3_GI_PREAUTHORITY_REVIEW.md`): **no** en opioide, ACS, edema pulmonar,
      embolia ni asma; el estado de colapso o consciencia del núcleo común es sólo estado fisiológico y **no termina un
      encuentro**;
    - registro: `docs/revision/PHASE2_AMENDMENT_2.md` (la Enmienda 1: `docs/revision/PHASE2_AMENDMENT_1.md`) y, para su uso
      en la Fase 3, `docs/PHASE3_AMENDMENT_2_GI_SHADOW.md`;
  - `phase-3-runtime-integration` es la rama autorizada para el desarrollo de la Fase 3 (decisión docente
    del 2026-11-07), desde esa cabeza de cierre. La infraestructura de la Fase 3 vive **fuera** de
    `clinical_core/`: ningún paquete de la Fase 3 edita ese paquete, porque el digesto del núcleo vigente
    cubre todas sus fuentes y de él depende la reconstrucción del cierre;
  - el motor de familias heredado (`family_engine.py`) sigue siendo la **única** autoridad en tiempo de
    ejecución: `COMMON_CORE_RUNTIME_AUTHORITY = False`;
  - `clinical_core` funciona sólo en sombra, y en la Fase 3 también en vivo **sin autoridad**, detrás de una
    bandera apagada por omisión, invisible para el residente y ausente de la puntuación;
  - **excepción acotada (decisión docente del 2026-11-12, FD-P3-203):** la **autoridad de desarrollo de presión de GI** (`sbp`, `dbp`, `map` derivada; sólo `gi_bleed_57m` y `gi_bleed_72f`; sólo el
    entorno de desarrollo; con la instantánea de presión ya aprobada `gi_pressure_committed`, el linaje certificado activo y la concesión explícita, inmutable y con huella fijada
    `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1` *[2026-11-16, FD-PROMOTE-01 a FD-PROMOTE-07: la autoridad viva ejecuta ahora la instantánea ratificada `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1`
    con la concesión `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2`; la V1 y el punto anterior siguen registrados, históricos y legibles; `docs/PHASE3_GI_PRESSURE_PROMOTION.md`]* *[2026-11-17, FD-TONE-09 a FD-TONE-11: la concesión viva es `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3`, un **re-ligado puro de linaje** de la V2 —misma instantánea, mismos casos, sólo presión; la norepinefrina sigue **no concedida**—; la V1 y la V2 quedan registradas y reproducibles pero **no abren sesiones nuevas** por configuración ordinaria: sólo una reconstrucción histórica declarada (`MRS_PHASE3_HISTORICAL_RECONSTRUCTION`); `docs/PHASE3_COMMON_VASCULAR_TONE.md` §1]*, que es la décima condición de la compuerta; ninguna bandera sola, ni `COMMON_CORE_RUNTIME_AUTHORITY`, ni la concesión sola la activan). La consciencia
    común (V1 exacta) corre **junto** a ella sólo como superposición candidata de comparación (`FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON`), **no** escribe el `mental_status` vivo, **no** es visible al
    residente y sigue sin autoridad; no es despliegue a residentes, ni autoridad de producción, ni cambio del primer piloto;
  - fuera de esa excepción, no hay autorización todavía para:
    - darle autoridad en tiempo de ejecución;
    - cambiar lo que ve el residente (salvo los valores de presión del experimento de desarrollo);
    - migrar fisiología más allá del trabajo en sombra aprobado expresamente;
    - integrar el motor de casos generados (`clinical_physiology`).

  Fuente: encargo del 2026-10-21 y `docs/PHASE2_SHADOW_CORE.md`; para la Fase 3, los encargos del
  2026-11-07, `docs/PHASE3_RUNTIME_INTEGRATION.md` y las filas FD-P3-01 a FD-P3-16 del Decision File; para
  la enmienda y su integración, las filas FD-AMEND1-01 a FD-AMEND1-04, FD-P3-119 y FD-P3-129; para la Enmienda 2 y
  su integración en la sombra GI, las filas FD-P3-167 a FD-P3-172; para la instantánea de GI y la revisión previa a la autoridad, FD-P3-178 a FD-P3-187;
  para la plomería **dormida** del par presión + consciencia (vista explícita de `mental_status`, `EXECUTED_NO_COMMON_PHYSIOLOGY`, rutas del reloj, un solo gancho; **sin** autoridad, V1 sigue sólo ratificada para
  desarrollo), `docs/PHASE3_DORMANT_PAIR_AUTHORITY.md` y FD-P3-188 a FD-P3-194; para el sitio **dormido y no activable** de autoridad GI del par (primitiva de validación por minuto, R2 reparado, puerta de armado sin concesión, máquina de estados, artefacto y
  replay; veredicto A que **no habilita nada**), `docs/PHASE3_DORMANT_GI_AUTHORITY_SITE.md` y FD-P3-195 a FD-P3-202; para las decisiones docentes de C1 y C5 y el **primer experimento real de autoridad de desarrollo de
  presión de GI** (concesión, activación, página real, serie de manejo, superposición de consciencia, fallos tras el compromiso, frontera de colapso, artefacto y replay, aislamiento, revisión independiente y punto de control),
  `docs/PHASE3_PRESSURE_DEVELOPMENT_AUTHORITY.md` y FD-P3-203 a FD-P3-208; para la **parada efectiva** de ese experimento (tras el primer compromiso real y un fallo posterior la sesión **no continúa**; sin retroceso al heredado; sin semántica terminal;
  sólo salir resuelve), `docs/PHASE3_EFFECTIVE_AUTHORITY_STOP.md` y FD-P3-209 a FD-P3-212; para el **turno controlado por la autoridad** de ese experimento (tras el primer compromiso real, un turno que la autoridad rechaza **no ocurre en el encuentro real**: se ejecuta sobre copias y se aplica sólo si la autoridad lo valida; sin retroceso, sin segundo motor, sin semántica terminal) y el **ancla de procedencia durable** que impide que un encuentro antes autoritativo vuelva a verse como heredado, `docs/PHASE3_AUTHORITY_TURN_TRANSACTION.md` y FD-P3-213 a FD-P3-216; para el **entorno docente de revisión controlada** de ese experimento (decisión docente del 2026-11-13: sólo desarrollo, sólo docentes, un solo proceso, sólo los dos casos de GI y sólo presión; ni piloto con residentes, ni producción, ni autoridad de consciencia, ni validación clínica; el registro sin firma se acepta como limitación **sólo** para esa revisión de un proceso), `docs/PHASE3_FACULTY_REVIEW_ENVIRONMENT.md`, FD-FAC-01 a FD-FAC-10 y FD-P3-217 a FD-P3-220; para la **revisión de trayectorias docente** (flujo separado y principal de esa revisión: una pantalla por escenario sobre trayectorias certificadas ya almacenadas, primera impresión ciega e inmutable, comparador heredado sólo tras el bloqueo, vinculación y resumen automáticos; sólo capa de UX, sin cambio de fisiología ni de autoridad), `docs/PHASE3_FACULTY_TRAJECTORY_REVIEW.md` y FD-UX-01 a FD-UX-08; para la **primera revisión docente humana** de esas trayectorias (siete escenarios: `ACCEPT` 1, `ACCEPT_WITH_LIMITATION` 5, `RECALIBRATE` 1 —FR-G—, `REJECT` 0; evidencia humana separada del análisis del modelo; **FR-G abierto a decisión docente**: veredicto `B`, nada ejecutable cambió, la norepinefrina queda como hoja de ruta de alta prioridad y no se implementa), `docs/PHASE3_FIRST_FACULTY_REVIEW_ANALYSIS.md`, FD-REVIEW-01 a FD-REVIEW-06, FD-P3-221 a FD-P3-224 y `TD-147`; para la **escala absoluta de la tasa de sangrado GI reabierta** tras esa revisión (2,5 mL/min es referencia histórica de desarrollo, no una tasa identificada clínicamente; la tasa sólo se identifica junto con la escala de presión; **sin** tasa ni parámetro aprobados, sin `FR-G_V2_CANDIDATE`, Enmienda 3 sin abrir, pendiente del ancla docente de respuesta a la sangre), `docs/PHASE3_GI_BLEED_RATE_SCALE.md`, FD-RATE-01 a FD-RATE-08, FD-P3-225 a FD-P3-229 y `TD-148`; para la **factibilidad conjunta tasa × presión** con las anclas docentes de glóbulos (una unidad ≈ +8 a +18 mmHg) y de cristaloide lento (≈ 15–35 % evitado) (intersección `NONEMPTY` con la fisiología actual, compuerta `A`: la Enmienda 3 **no** se abre; **sin** punto elegido ni parámetro aprobado; lectura de la ventana confirmada por FD-RATE-14: unidad completa al minuto 30), `docs/PHASE3_GI_JOINT_FEASIBILITY.md`, FD-RATE-09 a FD-RATE-13, FD-P3-230 a FD-P3-233 y `TD-149`; para la **región conjunta formalizada** y el **paquete de re-revisión humana ciega** (región en coordenadas enlazadas `tasa/escala`, escala y núcleo de cristaloide: la tasa nunca es un rango aparte; banda `CANDIDATE` [600; 1500] de la escala marcada `SUPERSEDED_BY_JOINT_FEASIBILITY_ANALYSIS` **fuera** del núcleo; testigos de prueba `LOW`, `CENTER_REFERENCE` y `HIGH`, **ninguno** elegido ni calibrado *(al 2026-11-15; el 2026-11-16 `CENTER_REFERENCE` se eligió como instantánea de desarrollo, ver la ratificación, abajo; no es una calibración)*; candidatos `JOINT_REGION_V1_CANDIDATE` de FR-B, FR-C, FR-E y FR-G **sometidos a la re-revisión humana ciega, reportada como completada el 2026-11-16** (ver la ratificación, abajo), sin transferir juicios anteriores; Enmienda 3 cerrada; nada ejecutable cambió), `docs/PHASE3_GI_JOINT_REGION.md`, `faculty_review_kit/region_conjunta_v1/`, FD-RATE-14 a FD-RATE-20, FD-P3-234 a FD-P3-239 y `TD-150`; para la **re-revisión docente interactiva y ciega** de esa región (la misma *Faculty Trajectory Review* sobre un conjunto versionado y fijado, `GI_JOINT_REGION_V1_FACULTY_REREVIEW`: sólo `CENTER_REFERENCE`, sólo FR-B, FR-C, FR-E y FR-G, sin comparador ni revelado, con el bloqueo de la primera impresión irreversible; es la re-revisión lo que se abre al iniciar sesión y, desde el parche de ciego, la primera revisión y el modo en vivo **no se ofrecen** hasta «RE-REVIEW COMPLETE · 4 / 4»; **sólo** capa de UX y plomería de revisión: ni fisiología, ni parámetros, ni trayectorias, ni autoridad; la re-revisión humana quedó **reportada como completada el 2026-11-16**, ver la ratificación), `docs/PHASE3_FACULTY_REREVIEW_INTERACTIVE.md`, FD-REREVIEW-01 a FD-REREVIEW-10, FD-P3-240 a FD-P3-245 y `TD-151`; para el **parche de ciego previo a la re-revisión humana** (decisión docente del 2026-11-16: mientras la re-revisión esté incompleta el lanzador **retiene** la primera revisión y el modo en vivo —retención de procedimiento, no una desactivación global— y falla cerrado; tras el 4/4 vuelven; la primera pasada **no muestra la FC ni el relleno capilar**, que no se recalcularon para el candidato; se conserva la redacción certificada de FR-G; interruptor nuevo del operador `MRS_FACULTY_REREVIEW_GATE=off`; sólo capa de UX: ni fisiología, ni parámetros, ni candidatos, ni autoridad), `docs/PHASE3_FACULTY_REREVIEW_INTERACTIVE.md` §14, FD-REREVIEW-21 a FD-REREVIEW-24 y FD-P3-246 y FD-P3-247; para la **ratificación de la región conjunta y el cierre de la calibración de presión de GI para desarrollo** (decisión docente del 2026-11-16 tras la re-revisión humana ciega: `ACCEPT` 1, `ACCEPT_WITH_LIMITATION` 3, `RECALIBRATE` 0, `REJECT` 0; `GI_JOINT_RATE_PRESSURE_DEVELOPMENT_REGION_V1` queda `RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS` con su estructura correlacionada; `CENTER_REFERENCE` es `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1`, el enlace exacto ya certificado, **copiado y no recalculado**, una **instantánea de desarrollo** —no calibración clínica, ni autoridad de producción, ni validación con residentes— que es un **registro que nada ejecutable lee** y **no** está vinculada a la autoridad viva *[situación al momento de la ratificación; **desde el 2026-11-16 (ciclo de promoción) sí está vinculada** a la autoridad viva de desarrollo, con la concesión V2: `docs/PHASE3_GI_PRESSURE_PROMOTION.md`]*; `LOW` y `HIGH` siguen siendo testigos de prueba; limitación monitoreada `GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE` sin recalibración; estado `GI_PRESSURE_DEVELOPMENT_CALIBRATION_CLOSED`, sólo desarrollo; Enmienda 3 cerrada; el registro humano es **reportado, no verificado contra el almacén persistido**; siguiente prioridad, **sin implementar**: vía común de tono vascular / vasopresor), `docs/PHASE3_GI_JOINT_REGION_RATIFICATION.md`, FD-RATIFY-01 a FD-RATIFY-07, FD-P3-248 a FD-P3-251 y `TD-152`; para la **promoción de esa instantánea a autoridad viva de desarrollo** (decisión docente del 2026-11-16: la autoridad de presión de GI ejecuta exactamente `GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1` mediante `runtime_pressure_snapshot.py` y la concesión versionada `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2`; **sin** núcleo sucesor —veredicto A—, sin calibración nueva, sin `LOW`/`HIGH`, sin Enmienda 3, sin norepinefrina ni control de fuente, sin autoridad de consciencia ni terminal, sin despliegue a residentes y sin validación clínica; la limitación `GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE` sigue monitoreada; la V1 sigue registrada y **retirarla de la activación es una decisión docente pendiente**; los registros históricos no se regeneraron), `docs/PHASE3_GI_PRESSURE_PROMOTION.md`, FD-PROMOTE-01 a FD-PROMOTE-07, FD-P3-252 a FD-P3-256 y `TD-153`; para la **vía común de tono vascular y el primer vasopresor** (decisión docente del 2026-11-17: Enmienda 3 del núcleo común —un estado general, el soporte vasoconstrictor, que multiplica el objetivo de tono; la norepinefrina a tasa fija es su **primer** escritor; sin ecuación «fármaco → mmHg»— **sólo en la sombra y apagada por omisión**; mapeo de desarrollo `runtime_tone_support.py` que ningún adaptador registrado usa; la autoridad viva **sigue deteniéndose** ante la orden de norepinefrina; FR-F es un **candidato versionado sin veredicto**, pendiente de decisión docente sobre su revisión humana; región de desarrollo con tres testigos, **ninguno elegido ni calibrado**; concesión V3 de re-ligado; V1 y V2 no seleccionables para sesiones nuevas; contrato de versionado de registros históricos: un registro generado es inmutable y una representación nueva es un registro sucesor; sin recalibrar GI, sin control de fuente, sin autoridad de consciencia ni terminal, sin despliegue a residentes y sin validación clínica), `docs/PHASE3_COMMON_VASCULAR_TONE.md`, `docs/PHASE3_HISTORICAL_RECORD_VERSIONING.md`, `docs/revision/PHASE2_AMENDMENT_3.md`, FD-TONE-01 a FD-TONE-12, FD-RECORD-01 a FD-RECORD-04, FD-P3-257 a FD-P3-264, `TD-154` y `TD-155`; para la **revisión docente multiescenario de esa vía** (decisión docente del 2026-11-18: cinco trayectorias de presión ante **una** orden de norepinefrina —hemorragia digestiva, sonda sintética de bajo tono, ACS, edema pulmonar, embolia pulmonar; opioide y asma excluidos por falta de sentido clínico—, sólo `CENTER_REFERENCE` y con lo ya certificado, **sin física nueva ni testigo elegido**; la misma *Faculty Trajectory Review* —Q1 a Q5, bloqueo de la primera impresión, juicio global, resumen—, sensibilidad LOW/CENTER/HIGH **opcional y sólo después** de todos los juicios, limitaciones **sólo** en el resumen final; sólo capa de UX y persistencia: **la revisión humana no se hizo**, ni autoridad de norepinefrina, ni despliegue a residentes, ni validación clínica), `docs/PHASE3_COMMON_TONE_FACULTY_REVIEW.md`, FD-TONEREV-01 a FD-TONEREV-07, FD-P3-265 a FD-P3-268 y `TD-156`.

## Privacidad y procedencia
- No commitear datos reales, respuestas externas, secretos ni nombres de médicos.
- No escribir la identidad del modelo del asistente de código en commits, comentarios ni archivos del repositorio.
  - En los commits, la atribución va como «Co-Authored-By: Claude <noreply@anthropic.com>», sin nombre ni versión
    del modelo (decisión del 2026-10-05). Los commits anteriores no se reescriben.
- Sí conservar la procedencia de los análisis de IA de la aplicación en el almacenamiento autorizado de cada
  ejecución (la base de la app), como ya se hace:
  - modelo o proveedor cuando corresponda;
  - versión del prompt;
  - fecha;
  - referencia a la evidencia.
- Nunca registrar secretos.

## Eficiencia (permanente)
OBTENER EL MISMO O MEJOR RESULTADO CON EL MÍNIMO USO INNECESARIO DE TOKENS, CONTEXTO, LLAMADAS DE IA Y CÓMPUTO.
- Recuperación focalizada antes de leer el repositorio; ampliar el contexto sólo si falta evidencia.
- Reutilizar auditorías, decisiones, matrices y pruebas verificadas, comprobando su vigencia cuando importe.
- Preferir código, búsquedas y pruebas deterministas. No pedir a la IA lo que dan los datos estructurados.
- Agrupar trabajo relacionado sin eliminar verificaciones independientes necesarias.
- No duplicar el mismo análisis extenso en varios documentos.
- Pruebas focalizadas durante el desarrollo; suite completa sobre un candidato estable cuando el riesgo lo
  justifique.
- Cargar sólo las skills y los documentos que la tarea necesita.
- Prevalecen sobre el ahorro: la calidad clínica, la fidelidad del Trace, la integridad de los datos, la
  reproducibilidad y el resultado final.
- Aplicar el presupuesto vigente sin inventarlo. Si un costo no se puede medir, decirlo: «0 llamadas de la app» no
  es «costo total cero».

## Skills del proyecto
Están en `.claude/skills/`. Se cargan cuando la tarea coincide con su descripción, y también a mano con
`/verificar-y-entregar` o `/ux-antes-despues`. Dicen cómo trabajar; no amplían ninguna autorización.
- `verificar-y-entregar`: al cerrar un cambio de código o de comportamiento (verificar → informar → entregar por
  git sólo si está autorizado).
- `ux-antes-despues`: ante un cambio de pantalla o de presentación (registro, navegador y capturas ANTES/DESPUÉS,
  con red y credenciales aisladas).
