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
    integrado en `phase-3-runtime-integration` el 2026-11-11. Es lo que hay hoy en `clinical_core/` de esa rama:
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
  - no hay autorización todavía para:
    - darle autoridad en tiempo de ejecución;
    - cambiar lo que ve el residente;
    - migrar fisiología más allá del trabajo en sombra aprobado expresamente;
    - integrar el motor de casos generados (`clinical_physiology`).

  Fuente: encargo del 2026-10-21 y `docs/PHASE2_SHADOW_CORE.md`; para la Fase 3, los encargos del
  2026-11-07, `docs/PHASE3_RUNTIME_INTEGRATION.md` y las filas FD-P3-01 a FD-P3-16 del Decision File; para
  la enmienda y su integración, las filas FD-AMEND1-01 a FD-AMEND1-04, FD-P3-119 y FD-P3-129; para la Enmienda 2 y
  su integración en la sombra GI, las filas FD-P3-167 a FD-P3-172; para la instantánea de GI y la revisión previa a la autoridad, FD-P3-178 a FD-P3-187;
  para la plomería **dormida** del par presión + consciencia (vista explícita de `mental_status`, `EXECUTED_NO_COMMON_PHYSIOLOGY`, rutas del reloj, un solo gancho; **sin** autoridad, V1 sigue sólo ratificada para
  desarrollo), `docs/PHASE3_DORMANT_PAIR_AUTHORITY.md` y FD-P3-188 a FD-P3-194.

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
