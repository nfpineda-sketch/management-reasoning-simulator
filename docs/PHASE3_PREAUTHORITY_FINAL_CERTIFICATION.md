# Fase 3 · P3-25 · Certificación final antes de una concesión de autoridad

Sólo lectura, más la corrida de pruebas que la sostiene. Pregunta única: **si la docencia eligiera mañana
una instantánea y concediera autoridad por escrito, ¿estaría el repositorio técnicamente listo para correr
el primer experimento de autoridad de presiones en GI, sólo en desarrollo?**

Candidato certificado: rama `phase-3-runtime-integration` sobre `4e44e4e`, con el paquete P3-19…P3-24.
Corridas sobre ese candidato: **334 aprobadas** en el grupo de autoridad, sombra, aislamiento, cierre de la
Fase 2 y documentos; **912 aprobadas** en el grupo de acciones, suerte de órdenes, persistencia, piloto,
batería de aceptación, guardas y español; **56 de 56** scripts de regresión activos (10 retirados, no
corridos, por decisión del propio ejecutor). Cero fallos.

## 1 · Lista de comprobación técnica (P3-25A)

| | Pieza | Resultado |
|---|---|---|
| 1 | Sitio de llamada de autoridad | **sí**, y dormido: un punto de orquestación, 0,13 µs por turno y cero digestos con la bandera apagada |
| 2 | Puerta | **sí**: nueve condiciones, reevaluadas en el commit, identidad desde el estado, secretos no honrados |
| 3 | Atomicidad | **sí**: una escritura o ninguna; el estado del llamador nunca se muta; un minuto es una transacción |
| 4 | Propiedad | **sí**: `sbp`/`dbp` comunes, `map` como lo deriva la pantalla, 16 heredadas, 4 sólo comparación |
| 5 | Elegibilidad | **sí**: 26 válidos y 8 inelegibles de 34, con una sola regla para las dos lecturas |
| 6 | Fallo por acción no soportada | **sí**: cuatro clases bloqueadas, tres formas de clave, clase desconocida y sin tipo incluidas |
| 7 | Mecanismo del registro de instantáneas | **sí, y deliberadamente sin puerta de configuración**: no hay forma de registrar una aprobación sin editar el módulo, así que activar exige un cambio de código revisable, no una variable de entorno |
| 8 | Aislamiento de la aprobación de prueba | **sí**: registro de sólo lectura, inyección por un nombre privado que el escaneo de producción vigila, sin artefacto y sin rastro en el Decision File |
| 9 | Procedencia | **sí**: 30 campos por minuto, incluida la entrada inmutable de ese minuto |
| 10 | Artefacto del experimento | **sí**: completo, verificable, con su digesto sobre todo el contenido |
| 11 | Retroceso | **sí**: materializado al refutar, con los catorce campos y el minuto reproducible |
| 12 | Replay | **sí**: tres minutos reales reproducidos desde el artefacto solo, con tres digestos distintos |
| 13 | AppTest | **sí**: la app dibuja las presiones comprometidas; una refutada deja las heredadas; su propio caso no es GI y no admite commit |
| 14 | Exclusión del piloto | **sí**: anclada a `pilot_freeze.RUNTIME_FLAGS`, fallando cerrada si no se puede leer |
| 15 | Inmutabilidad de la Fase 2 | **sí**: digesto `22b90a6f7f38…` recalculado; `clinical_core/`, `family_engine.py` y `pilot_freeze.py` sin cambios desde `d2cca46` |
| 16 | Imposibilidad de retroceso silencioso | **sí**: un fallo detiene la autoridad del encuentro y lo declara; no hay alternancia minuto a minuto |
| 17 | Sin impacto en la puntuación | **sí**: ninguna fuente de puntuación, rúbricas, radar ni D1–D5 cambia, y el grupo de 912 pruebas lo cubre |

## 2 · Bloqueos técnicos que quedan (P3-25B)

**Uno.** La **superficie docente del experimento**: dónde se muestra un fallo duro y dónde se guarda el
artefacto. Hoy el artefacto vive en la sesión, `authority_status()` es la lectura única que una superficie
necesitaría, y nada lo dibuja ni lo persiste. La consecuencia concreta: un fallo duro durante el primer
experimento sería invisible en pantalla, lo que contradice la política de fallo declarada
(`HARD_FAIL_VISIBLE_TO_FACULTY`).

No lo construí por tres razones, y las tres son del encargo: toca la pantalla; toca la persistencia; y
**dónde vive el artefacto es la decisión docente F** de `docs/PHASE3_FACULTY_AUTHORITY_DECISION_PACK.md`.

No cuento como bloqueo técnico ninguna decisión docente pendiente (A–G del pack), ni la ausencia de un
mecanismo de registro de instantáneas (fila 7: su ausencia es la protección), ni las cuatro diferencias
parcialmente declaradas que están fuera del dominio de presión.

## 3 · Veredicto (P3-25C)

**`ONE_TECHNICAL_PACKAGE_REMAINS`**

Todo lo que una autoridad limitada de presiones necesita está construido, probado de extremo a extremo y
dormido: 17 de 17 comprobaciones de la §1 pasan. Lo que falta es un paquete pequeño y bien delimitado —una
lectura ya existe; faltan una superficie y una decisión de almacenamiento— y siete decisiones docentes.

## 4 · Por qué no emito la plantilla de autorización futura (P3-25D)

La plantilla corresponde al veredicto `TECHNICALLY_READY_FOR_FACULTY_AUTHORITY_GRANT`, y este veredicto no
es ése. Emitirla ahora invitaría a conceder autoridad sobre un experimento cuyo fallo duro nadie vería.

Lo que sí está listo para la docencia, sin autorizar nada: las siete decisiones exactas (A–G) con su
material, sus candidatos medidos y sus riesgos, en `docs/PHASE3_FACULTY_AUTHORITY_DECISION_PACK.md`; la
decisión F de ese pack es, además, la que desbloquea el único paquete técnico que queda.
