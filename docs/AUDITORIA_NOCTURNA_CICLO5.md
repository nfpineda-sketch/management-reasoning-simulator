# Auditoría nocturna del ciclo 5 (59A–59BU)

2026-09-28 · rama `clinical-encounter-v0.13` · código auditado: el ENGLISH
VALIDATION BASELINE (`ec1c77f`) más la única corrección de la noche (59Z).

## Cómo se hizo

- **Cinco auditorías en paralelo** (agentes) y la sesión principal:
  - aislamiento, idempotencia, concurrencia y transacciones;
  - integridad longitudinal y procedencia;
  - oportunidades TD/F/C;
  - Management Trace y jugabilidad;
  - brechas del banco de casos.
- **Sólo datos sintéticos.**
  - Cuentas, encuentros y valoraciones docentes de prueba, rotulados como
    tales, en bases SQLite desechables que se borraron al terminar.
  - Ninguna llamada a proveedores de IA.
  - Ningún dato real: la base del despliegue no se tocó.
- **La sesión principal verificó en el código** los hallazgos que suben a
  este documento. Donde no, se dice.
- **Límite de corrección (59AU, 59BT, 59I).** Por defecto, auditar y
  documentar.
  - Hubo **una sola corrección**: 59Z, un bug inequívoco de aislamiento y
    persistencia, pequeño, reversible y probado.
  - Todo lo demás queda documentado con su corrección propuesta, sin aplicar.
- **Dónde está la evidencia.** Los guiones y salidas de las auditorías
  quedaron en el espacio temporal de la sesión, fuera del repositorio. Cada
  hallazgo cita archivo y línea, y se reproduce con lo que se describe.

**Documentos de esta auditoría:**

| Documento | Ítems |
|---|---|
| este documento | índice, integridad, longitudinal, escala, reproducibilidad, consistencia, inconsistencias clínicas, *release readiness* |
| `AUDITORIA_TRACE_CICLO5.md` y `AUDITORIA_TRACE_FRASES_CICLO5.md` | 59G, 59H, 59O |
| `tdfc/BORRADOR_TDFC.md`, `tdfc/DECISIONES_TDFC.md`, `tdfc/MATRIZ_OPORTUNIDADES.md` | 59B, 59C, 59D |
| `AUDITORIA_BRECHAS_BANCO_CICLO5.md` | 59E, 59F, 59BI, 59BJ, 59BK |
| `SOURCE_OF_TRUTH_MAP.md`, `DATA_DICTIONARY.md`, `ARQUITECTURA.md`, `CAMBIOS_METODOLOGICOS.md`, `REGISTRO_DEUDA_TECNICA.md`, `NEXT_ACTIONS.md`, `PRIORIZACION_POST_PILOTO.md` | 59AL, 59BN, 59BO, 59BP, 59BQ, 59BR, 59S |

## Resumen

| # | Hallazgo | Severidad | Estado |
|---|---|---|---|
| 1 | **El lector pierde órdenes de primera línea por la forma de la oración.** «Anafilaxia: adrenalina 0,5 mg IM ahora…» o «Atropina 1 mg ev, si no responde, marcapaso…» no ejecutan nada: la frase entera queda como plan. Con un punto en vez de «:» o «,», sí. Son 9 clases CRITICAL | CRITICAL | Documentado (59I). **No es regresión:** las 90 frases se leen igual en `939978a` y hoy |
| 2 | **La página dice «Urgent intervention executed» cuando nada corrió**, y ofrece explicarla después (59O-03, C08) | CRITICAL | Documentado |
| 3 | **Un encuentro heredaba el cierre del anterior** (59Z): el aviso de cierre y el registro de cierre | MEDIUM | **Corregido** (C-2026-09-28-03), con 3 pruebas en la página real |
| 4 | **Los temas de historia se leen del banco vivo, no del caso congelado** (F-01): un cambio del banco reinterpreta encuentros antiguos, también el tamizaje de un evento crítico | MEDIUM | Documentado |
| 5 | **POCUS de las 4 oclusiones coronarias:** la severidad redactada al llegar baja a «mildly reduced» en el primer POCUS repetido, con la arteria cerrada. En de Winter (C14 YES): acinesia → «mildly reduced» a los 30 min → acinético a los 100 | MEDIUM (clínico) | Decisión docente |
| 6 | **El perfil D1–D5 ordena por fecha de confirmación, no del encuentro** (F-04): «último encuentro» y «cambio» pueden decir lo contrario de la trayectoria | MEDIUM (diseño) | Decisión |
| 7 | **La cola docente completa tarda 14,5 s con 5000 encuentros pendientes.** Hoy son 0,3 s con 100 | MEDIUM a escala | Documentado |
| 8 | **El aislamiento entre residentes se sostiene:** 36 métodos rechazan a otro residente | — | PASA |
| 9 | **La idempotencia, la concurrencia y las transacciones se sostienen**, con respaldo en la base | — | PASA |
| 10 | **El oráculo longitudinal coincide en cada celda** calculada a mano | — | PASA |

---

## 1. Integridad de datos: residentes, encuentros, idempotencia, concurrencia (59Y, 59Z, 59K, 59L, 59AH, 59BA, 59BB, 59AA, 59BC, 59AG)

**Sin hallazgos CRITICAL ni HIGH.** Ocho guiones: 166 comprobaciones se
comportan como se describe y 2 fallan, ambas por I-F02.

- **Entre residentes (59Y).**
  - El token del residente B fue rechazado en los 36 métodos públicos de
    lectura y escritura probados sobre datos del residente A.
  - Lo que B sí puede leer (su progreso, su perfil, su exportación) no trae
    nada de A.
  - Reusar identificadores de otro encuentro se rechaza: brief, propuesta,
    referencias de evidencia.
- **Idempotencia (59L, 59AH).**
  - Valorar dos veces el mismo encuentro y objetivo devuelve «duplicate»: una
    fila y una entrada de auditoría.
  - Reabrir, anular o fijar la meta dos veces no cambia nada.
  - Guardar dos veces la misma revisión se rechaza.
  - **Doble clic en «Submit»:** el formulario se vacía al enviar
    (`clear_on_submit=True`) y un envío vacío se ignora, así que no duplica la
    orden. Verificado leyendo el código, no con la página.
  - **Reenviar una orden** es un turno nuevo, por diseño. Si el motor la repite
    depende del fármaco: una dosis única ya dada no se repite
    (`family_engine.py:1074`).
- **Concurrencia (59BA).** 25×4 hilos y 10×4 procesos valorando a la vez:
  siempre una sola observación activa. El respaldo es un índice único parcial,
  `BEGIN IMMEDIATE` en SQLite y un *advisory lock* en PostgreSQL.
- **Transacciones (59BB).** Una falla inyectada tras la última escritura
  deshace todo, y un proceso muerto a mitad de transacción no deja nada.
- **Confirmación (59AA).** Un brief de IA «satisfactorio», una propuesta de
  rúbrica o un borrador nunca cuentan.
- **Recuperación (59AG).**
  - Recargar la página docente y confirmar de nuevo no duplica.
  - Retomar un encuentro guardado conserva su orden retenida
    (`test_pending_order_recovery.py`) y su aviso de cierre (prueba nueva).
  - Los informes de IA se guardan por huella del encuentro: regenerarlos no
    cambia la evidencia.

### 59Z: un encuentro nuevo heredaba el cierre del anterior (CORREGIDO)

Reproducido en la página real antes de corregir:

| Paso | Qué pasaba |
|---|---|
| Encuentro N: «Complete Encounter» sin destino | aparece el aviso «How is this encounter ending?» |
| El residente abandona N y empieza N+1 | **N+1 abre en el minuto 0, sin nada hecho, con el aviso y el botón «Finish now»** |
| N se cierra («clinical_close», minuto 2) y se empieza N+1 | **el registro de cierre de N se guarda en N+1**; si N+1 se abandona, queda en él |

- **Por qué importa.** El brief docente y el tamizaje de la rúbrica leen ese
  registro como el cierre de N+1.
- **Corrección.** `reset_session()` quita `close_pending` y
  `encounter_close`, como ya quitaba el idioma del encuentro. Son 2 líneas.
- **Pruebas** (`test_a_new_encounter_starts_without_the_last_close.py`):
  - el aviso no pasa al encuentro siguiente;
  - el registro no pasa, ni al abandonarlo;
  - control positivo: un encuentro **retomado** conserva su propio aviso, y
    uno cerrado su propio registro.
  - Sin la corrección fallan las 3.
- **Lo que no se hizo:** los registros ya guardados no se reescribieron. Un
  encuentro abandonado con un `encounter_close` y sin `encounter_ended` es
  sospechoso de venir de otro. Se puede listar con una consulta de lectura
  cuando usted lo autorice.
- Registrada como **C-2026-09-28-03**.

### Hallazgos que quedan (sin corregir)

| ID | Severidad | Hallazgo | Evidencia | Corrección propuesta |
|---|---|---|---|---|
| I-F02 | LOW (bug) | La exportación del residente trae `reviewed_by` vacío siempre: `RubricStore.progress()` no lee el nombre del revisor | `rubric_store.py:417-432`; `resident_portal.py:273` | Unir `mrs_users` y devolver `reviewer`; prueba en la exportación |
| I-F18 | LOW-MEDIUM | Al migrar una base antigua, la foto de una confirmación absorbe observaciones posteriores a ella | `progress_store.py:162-167` | Tomar sólo las de `created_at` ≤ la confirmación |
| I-F09 | LOW | Crear el encuentro y consumir la directiva docente son dos transacciones | `curriculum_runtime.py:220, 223` | Una transacción |
| I-F06 | LOW | Las columnas `sequence` no tienen restricción única; son correctas por el bloqueo global | `rubric_store.py:180-233` y otras | `UNIQUE(attempt_id, …, sequence)` |
| I-F19/20 | LOW | Duplicados previos o un `provenance_json` corrupto tiran la vista de progreso con «base no disponible» | `progress_store.py:99-100, 261-270` | Revisarlo en `check_database.py`; decodificar fila por fila |
| I-F10 | LOW | Ese mensaje se usa para todo error, incluso de programación, y no se registra | `account_store.py:252-256` | Registrar la clase del error en el servidor |
| I-F24 | LOW | `save_draft` acepta un borrador de C14 en un caso NO (sólo llamando al almacén; nunca cuenta) | `progress_store.py:462-474` | Revisar la elegibilidad al guardar |
| I-F25 | INFO | `get_progress` con token de residente devuelve la evidencia esperada y la razón del caso, IDs docentes y el motivo de anulación. No se muestran ni se exportan hoy | `progress_store.py:260-270, 306` | Quitarlos antes de exportar observaciones al residente |
| I-F17 | INFO | La prueba de migración «sin perder filas» no inserta ninguna fila | `test_progress_store` | Agregar una fila |

### Decisiones que surgen (59BC)

1. **Una observación anulada:** hoy el residente ve el juicio anulado, sus
   notas y el motivo de la anulación (`progress_portal.py:95-97`). ¿Se
   mantiene, se oculta el motivo o se ocultan las filas anuladas?
2. **Retirar una rúbrica confirmada** es imposible hoy. Un borrador posterior
   deja publicada la revisión confirmada, mientras la pantalla docente muestra
   el borrador. ¿Se agrega un estado «retirada», o vale la última confirmada?
3. **Una meta subida después de confirmar** deja el objetivo «confirmado»
   bajo la meta nueva (2/5). ¿Se marca para revisión o se mantiene?

---

## 2. Integridad longitudinal y procedencia (59J, 59AY, 59AI, 59AZ, 59BD, 59AB, 59AC, 59BE)

**Sin hallazgos CRITICAL ni HIGH.** La tubería, la aritmética del perfil y la
independencia del orden son correctas.

- **Tubería (59J), 14 de 14:**
  - una observación cuenta una vez;
  - varios vínculos no multiplican la cuenta, y DIRECT/PARTIAL no es un peso;
  - una oportunidad NO no da nada, y una YES sin desempeño tampoco;
  - un borrador no confirma;
  - la confirmación y la procedencia sobreviven a una recarga;
  - los registros históricos siguen con su regla (legacy o transición);
  - C14 da 14 YES, 16 NO y `acs_54m_inferior` con la transición.
- **Oráculo (59AY, 59AI).** Una trayectoria de 9 encuentros calculada a mano
  coincide celda por celda con la aplicación:
  - D1 = 2, 3, 1, NE, 2 → n = 4, media 2,00;
  - tras un sexto encuentro: D3 media 1,83 (11/6), total ajustado medio
    11,0 = (10 + 12)/2, 4 eventos críticos;
  - totales, penalizaciones y cuentas de Objective Progress: iguales.
  - Los dominios no evaluables, los borradores y los encuentros sin valorar
    quedan fuera, y una rúbrica revisada cuenta una vez.
- **Orden (59AZ).** Con tres órdenes de inserción, son iguales las cuentas,
  las contribuciones, medias y n, eventos, total ajustado medio y alertas. Sólo
  cambian «último», «cambio» y el orden en pantalla (F-04).
- **Tiempo (59BD).** Todo se guarda en segundos de época y se muestra en UTC.
  Los problemas son los empates en el mismo segundo y el desfase de reloj
  entre servidores (F-02, F-03, F-06).
- **Mutación del caso (59AC).** Tras cambiar en memoria signos, laboratorio,
  POCUS, imagen, C14, eventos, dominios y vínculos, **16 lectores** del
  encuentro antiguo quedan estables: leen la copia congelada y su huella.
  **Sólo se mueven los temas de historia** (F-01).

### Reconstrucción desde la base sola (59AB, 59BE)

| Elemento | Estado | Cómo |
|---|---|---|
| Caso y su versión | RECONSTRUIBLE el contenido; PARCIAL la versión | copia completa y su hash; huella de la declaración; `code_version`. No hay etiqueta de versión por caso |
| Management Trace original | RECONSTRUIBLE | `payload_json`; un encuentro cerrado es de sólo lectura; `payload_sha` coincide |
| Foto de la oportunidad | RECONSTRUIBLE (legacy: vacío) | `provenance.opportunity`, con la revisión C14 firmada |
| Decisión docente | RECONSTRUIBLE | fila de observación y auditoría |
| Rúbrica | RECONSTRUIBLE (salvo F-02) | revisiones y propuestas sólo se agregan |
| Unidad de evidencia | RECONSTRUIBLE | `evidence_json` copia los ítems citados del Trace |
| Contribuciones al marco | PARCIAL | vínculos sólo para R1-03, R1-04 y R2-01 (TD-03) |
| Eventos críticos | PARCIAL | se guardan, pero el tamizaje se recalcula con los temas vivos (F-01) |
| Versión de motor y mapping | PARCIAL | por la base del encuentro |
| Imágenes | PARCIAL | bitácora de exhibición |

### Hallazgos que quedan (sin corregir)

| ID | Severidad | Hallazgo | Evidencia | Por qué no se corrigió |
|---|---|---|---|---|
| L-F01 | MEDIUM (bug) | Los temas de historia se leen del banco vivo, no del caso congelado. Si el caso pierde un tema, el encuentro antiguo lo muestra como no ofrecido; si gana uno, como «nunca preguntado». El tamizaje `bradycardia_cause_unexamined` pasa de «contradicho» a «lectura», lo que quita la exigencia de justificar su confirmación. Afecta el informe docente, el de la rúbrica, el formulario de eventos, la entrada del brief y el informe del residente | `history_review.py:126-133, 143`; `rubric_store.py:122-128` | Toca el tamizaje de eventos críticos, que no se cambia sin aprobación. **Hoy es latente**: el registro de correcciones no muestra ningún cambio de temas de historia en el banco. Si alguno ocurrió antes, los encuentros de antes ya se leen con los temas de hoy; eso sólo se sabría mirando la base del despliegue |
| L-F02 | LOW (bug) | El perfil elige la «última» rúbrica confirmada de un encuentro por hora, y el resto de la aplicación por número de revisión. Con un reloj 10 s atrasado: perfil D1 = 3 (revisión superada) y el residente ve D1 = 1 | `rubric_store.py:417-432` | Alimenta el radar, que no se cambia sin aprobación |
| L-F03 | LOW | Dos encuentros confirmados en el mismo segundo se ordenan por su propia revisión: «último» es el encuentro equivocado | `rubric_store.py:434`; `rubric_progress.py:53-54` | Ídem |
| L-F04 | MEDIUM (diseño) | La cronología del perfil es la de las confirmaciones. «Último encuentro» y «−2 respecto del anterior» se mostraron aunque el residente mejoró de 1 a 3 | `rubric_portal.py:485-487`; la fecha del encuentro se lee en `rubric_store.py:417` y se descarta | Decisión de producto |
| L-F05 | LOW (latente) | Una rúbrica de otra versión sale de la cuenta de eventos críticos (4) pero entra en las alertas (5). Las alertas se muestran sólo si la cuenta no es 0 | `rubric_portal.py:498-501`; `resident_portal.py:253` | Eventos críticos |
| L-F06 | LOW | Observaciones del mismo segundo salen en orden aleatorio (15 de 20 intentos) | `progress_store.py:304, 426` | Cosmético |
| L-F07 | LOW-MEDIUM (política) | C14 sigue abierto por la transición en casos generados por IA, en los encuentros PS001 (R1-03, R1-04, R2-01) y en los 9 candidatos del catálogo de hipoglicemia, aunque los casos de hipoglicemia del banco dicen NO | `observation_opportunities` | Decisión docente |
| L-F08 | LOW | Huecos de procedencia: vínculos de los 8 Decision Challenges (= TD-03); `ai_brief_id` sólo en la auditoría; sin versión del catálogo de objetivos | — | Diseño |
| L-F09 | LOW (latente) | `assess()` devuelve cuenta + 1 aunque no se cumpla una autonomía exigida. Ningún objetivo la exige hoy | `progress_store.py:460` | Lógica de progreso |
| L-F10 | LOW (latente) | Un evento crítico inventado se acepta (−3) si el caso no define ninguno. Todos definen al menos uno hoy | `rubric_store.py:114` | Eventos críticos |

---

## 3. Estrés y escala (59AV, 59AW, 59AX)

**Escala (59AX).** Residentes y encuentros sintéticos sobre la API real del
almacén, en una base desechable. Cada encuentro tiene una decisión, dos
valoraciones (TD1 y C14) y una rúbrica confirmada.

| Medida | 50 × 20 (1000) | 100 × 50 (5000) | ¿Crece? |
|---|---|---|---|
| Guardar un encuentro | 3,7 ms | 3,8 ms | no |
| Dos valoraciones docentes | 4,9 ms | 5,0 ms | no |
| Confirmar una rúbrica | 2,3 ms | 2,3 ms | no |
| Objective Progress de un residente | 1,6 ms | 2,5 ms | apenas |
| Perfil y radar de un residente | 1,6 ms | 2,3 ms | apenas |
| Procedencia de sus observaciones | 1,6 ms | 2,1 ms | apenas |
| Cola docente de un residente | 68 ms | 147 ms | lineal con sus encuentros |
| **Cola docente completa** | **3,2 s** | **14,5 s** | **lineal: 2,9 ms por encuentro pendiente** |
| Base | 10 MB | 51 MB | — |

- **Causa de la cola (perfilada):** el 98 % del tiempo es resolver la
  elegibilidad objetivo por objetivo. Casi todo eso es reconstruir y verificar
  la base congelada del encuentro, **17 veces por encuentro**
  (`competency_mapping.objective_is_eligible` → `evaluation_basis._from_frozen`).
  La página de «pendientes» la llama en cada interacción.
- **¿Es un problema hoy?** No: con el piloto (decenas de encuentros) es menos
  de medio segundo. Con una cohorte de 50 residentes y 20 encuentros cada uno,
  sí (3 s por clic).
- **Corrección propuesta, no aplicada:** resolver las oportunidades una vez
  por encuentro (`observation_opportunities.summary`) o guardar la base
  verificada por encuentro y revisión. Es la TD-09, que sube a MEDIUM.
- **C14 a escala:** el residente 1 tuvo 40 observaciones C14 en 50
  encuentros. Son exactamente los encuentros YES y de transición; los NO se
  rechazaron.

**Trayectorias sintéticas (59AW).** No se construyó una cohorte A–F aparte:
cada perfil pedido ya quedó cubierto con datos sintéticos por el oráculo y la
escala.

| Residente pedido | Dónde quedó cubierto |
|---|---|
| A · pocas observaciones | oráculo S1 (5 encuentros) |
| B · muchas observaciones | escala: 50 encuentros por residente |
| C · puntajes 0 | oráculo: D3 = 0 en E4 y E9 |
| D · eventos críticos | oráculo: 4 eventos, uno descartado, uno de otra versión |
| E · muchas contribuciones PARTIAL | tubería A2, A3: R2-01 con 4 DIRECT y 2 PARTIAL cuenta 1 |
| F · mismo objetivo en contextos distintos | TD1 en 4 casos distintos cuenta 4; C14 en 40 encuentros |

---

## 4. Reproducibilidad (59X) y rúbrica (59AD)

**Deterministas, comprobado:**

- **El lector, el motor, el Trace y la extracción del razonamiento.**
  - El corpus de ensayo (20 ES + 20 EN) dio lo mismo que en el ciclo 4,
    decisión por decisión.
  - Las 90 frases de la auditoría del Trace se leen igual en dos commits.
- **La resolución de oportunidades.** Se lee de la base congelada con su
  huella, y 16 lectores quedan estables tras mutar el banco.

**Variación esperable (generativa), que nunca cuenta como evidencia:**

- el brief docente;
- la propuesta de rúbrica;
- la síntesis del Trace;
- la traducción de prosa;
- los casos generados;
- las imágenes;
- la conversación con el paciente.

**Variación evaluativa inesperada: MISMA ACTUACIÓN → DISTINTA EVIDENCIA:**

1. **La forma de la oración** (hallazgo 1 del resumen). La misma decisión
   escrita con «.» se ejecuta, y con «:» o «, si no responde,» no. El Trace
   atribuye la omisión al residente.
2. **Los temas de historia vivos** (L-F01). El mismo encuentro cambia su
   tamizaje si el banco cambia.
3. **La hora de confirmación** (L-F02 a L-F04). El mismo conjunto de
   rúbricas da otro «último» y otro «cambio» según cuándo se confirmó.

**Rúbrica guardada → recargada → exportada (59AD).**

- D1–D5, lo no evaluable, los eventos, los totales y la confirmación se
  conservan en la base y tras recargar. Lo comprobaron el oráculo y las
  auditorías.
- **Discrepancia:** la exportación del residente no trae quién confirmó
  (I-F02).
- Los PDF no se regeneraron. Las pruebas existentes de documentos de rúbrica
  cubren su representación.

## 5. Consistencia entre informes (59AE) e idioma (59AF)

| La fuente dice | Un derivado dice | Dónde | Estado |
|---|---|---|---|
| Trace: `clarification_required`, nada ejecutado | la página: «Urgent intervention executed» | C08, 59O-03 | documentado |
| Trace: sólo la reevaluación | la página: «executed» (la orden perdida no aparece) | C02, C05–C07 | documentado |
| El caso congelado ofreció el tema X | informes docente y de rúbrica, formulario de eventos y brief: según el banco de hoy | L-F01 | documentado |
| Base: la rúbrica la confirmó un docente | exportación del residente: `reviewed_by` vacío | I-F02 | documentado |
| Encuentros en orden cronológico | perfil: «último encuentro» por confirmación | L-F04 | decisión |
| Cierre del encuentro N+1 | brief y tamizaje: el cierre del N | 59Z | **corregido** |

- **Idioma.** Las razones y la evidencia esperada de C14 se muestran en inglés
  en el portal en español (TD-07).
- **Mensajes del lector en inglés** dentro de la interfaz en español cuando el
  residente está trabado (59O-10, M12).
- El significado evaluativo no depende del idioma: se lee de la base
  congelada.

## 6. Management Trace y jugabilidad (59G, 59H, 59O)

- **Detalle:** `AUDITORIA_TRACE_CICLO5.md`.
- **Qué se probó:** 90 frases clínicamente naturales (46 EN, 44 ES), rotuladas
  INTERNAL AUDIT DATA, y 6 guiones en la página real.
- **Hallazgos nuevos:** 9 CRITICAL, 14 HIGH, 13 MEDIUM y 3 LOW, más 15
  fricciones.
- **Ninguno se corrigió (59I), y ninguno es regresión.**

**Las cinco fricciones que más traban a quien juega:**

1. **«Urgent intervention executed» sin que nada corriera** (CRITICAL).
2. **Preguntas atadas a órdenes mal leídas** (CRITICAL). Contestarlas puede
   ejecutar lo equivocado: el flujo para un oxígeno fantasma, una tasa de
   glucosa ante una insulina.
3. **«Please specify…»**, sin citar lo que no se leyó y sin español.
4. **«Registrado como plan»** junto a «Please specify…», con una orden no dada
   dentro de la cita.
5. **Todo o nada:** un fragmento dudoso retiene también el torniquete o la
   VMNI.

## 7. Oportunidades TD/F/C (59B, 59C, 59D)

- **Detalle:** `tdfc/`. **Es un borrador, nada está en el banco**: TD1, F1,
  C1, C3 y C4 siguen con la regla de transición.
- **De 155 combinaciones caso × objetivo:** 73 YES, 60 NO y 22 UNCERTAIN.
- **Las 22 dudosas caben en 8 decisiones** (TDFC-1 a TDFC-8), cada una con su
  recomendación.
- **Consecuencia que conviene saber antes de decidir:** si se aprueban TDFC-7
  y TDFC-8, **ningún caso del banco ofrece C4**. Al retirar la transición, C4
  dejaría de ser observable en el banco.
- **Las filas de `acs_54m_inferior`** se redactaron, pero no deberían
  activarse antes de DF-20.
- **Límites del motor que afectan la evidencia:**
  - en asma, el ventilador sólo se ajusta tras intubar;
  - `procedural_sedation` también registra la inducción de la intubación, lo
    que podría proponer C4 sobre algo que es C3.

## 8. Brechas del banco (59E, 59F, 59BI, 59BJ, 59BK)

- **Detalle:** `AUDITORIA_BRECHAS_BANCO_CICLO5.md`.
- **Las brechas grandes son de asignación, no de casos.** Lo que hace
  observable un desafío está en casos concretos, a veces fuera de sus familias.
  - R1-07 trae su elemento explícito en 1 de sus 9 casos
    (`acs_54m_inferior`).
  - R2-02 es SCA en un 75 %.
  - R1-03, R1-04 y R2-01 no tienen casos del banco, aunque su contenido está en
    8 a 31 casos.
- **Clases:** 8 de 18 brechas son A (declarar por caso o ajustar el sorteo), 2
  son B (un caso nuevo podría servir), 4 C y 4 D.
- **Redundancia:** `acs_61m_posterior` ≈ `acs_52m_de_winter` en el manejo, y
  `gi_bleed_57m` ≈ `gi_bleed_72f` salvo en D1.

## 9. Inconsistencias clínicas conocidas (59P)

Sólo hallazgos: **no se cambió ningún dato clínico**.

| Caso | Contradicción | Fuente A | Fuente B | Impacto posible | Severidad | Recomendación |
|---|---|---|---|---|---|---|
| `acs_54m_inferior` | VD comprometido frente a POCUS con VD normal | el caso y el motor (VD comprometido) | el POCUS redactado (VD normal) | el residente confía en el POCUS, da nitratos y la fisiología lo castiga | HIGH | DF-20 (`AUDITORIA_ACS_54M_INFERIOR.md`) |
| **las 4 oclusiones** (de Winter, posterior, inferior, tronco) | la severidad del VI redactada al llegar baja en el primer POCUS repetido, con la arteria cerrada | POCUS de llegada: «Akinesis…» (de Winter), «Hypokinesis…» (posterior), «Reduced…» (inferior), «Globally reduced…» (tronco) | POCUS a los 30 min, sin reperfusión: «mildly reduced» en los 4. De Winter vuelve a «akinetic» a los 100 min | en de Winter (C14 YES por decisión A) una mejoría aparente sin reperfusión puede leerse como reperfusión, y la evidencia esperada de C14 descansa en la evolución de la pared | MEDIUM | Decisión docente: qué representación es la correcta (generaliza TD-08). Verificado por la sesión principal en el motor |
| `bradycardia_bb_54f` | somnolienta en la presentación, «Alert» en el monitor | presentación: «found drowsy at home» | estado de llegada: `mental_status` = «Alert» | un dato de gravedad que no se ve al monitorizar | LOW-MEDIUM | Decisión docente. Verificado |
| `anaphylaxis_63m_betablocked`, `bradycardia_ccb_68m` | FA como antecedente, ritmo sinusal en el monitor | comorbilidades: fibrilación auricular (en 63m, además, apixabán y un «irregular heart rhythm» referido en la historia) | ritmo derivado de la FC: «Sinus rhythm» / «Sinus bradycardia» (`clinical_cases.py:204-205`) | el ECG y el monitor no muestran la FA que el caso declara | LOW-MEDIUM | Decisión docente. Verificado |
| Mujeres en edad fértil (p. ej. `pulmonary_embolism_33f`) | el estado de embarazo no está redactado | — | — | si alguien lo pregunta antes de la angio-TC, el caso no tiene respuesta | LOW | Decidir qué responde el caso |
| todo el POCUS del banco | los casos C14 YES descansan en un POCUS que el código llama borrador | `POCUS_DRAFT_PENDING_FACULTY_REVIEW = True` (`clinical_cases.py:64`) | C14 YES aprobado | — | MEDIUM | Confirmar el POCUS de los casos C14 YES (TD-04) |
| `obstructive_pyelonephritis_58f` | C14 YES, pero el POCUS repetido no está modelado | declaración C14 | motor | la evidencia esperada puede no ofrecerse | LOW | Revisar con C14 |
| `bradycardia_hyperk_63m` | peso seco sin definir | — | — | pendiente docente conocido | LOW | — |

## 10. Consistencia documental (59Q)

- Se buscaron los términos pedidos en toda la documentación: «objective
  automatically available», «target = observed», «PARTIAL como defecto», «EPA
  completed», «C14 globalmente disponible», «no trauma cases».
- **No quedó documentación vigente obsoleta.**
  - Los usos encontrados dicen lo contrario («sin contribución a la EPA
    completa», «PARTIAL no es un defecto»).
  - El docstring de `observation_opportunities.py` describe bien la transición
    y su retiro.
- Las auditorías y notas históricas no se reescribieron.

## 11. Dependencias y código muerto (59AM)

Barrido del grafo de imports de los 172 módulos del producto:

- **Ningún módulo del producto está muerto.** `setup_accounts` es la entrada
  de línea de comandos para crear cuentas.
- **Sólo lo usan pruebas o herramientas, y no están conectados a la
  aplicación:**
  - `c14_review`;
  - `check_database`;
  - `hypoglycemia_battery`;
  - `image_arrivals` e `image_pilot`;
  - `tanda20_en` y `tanda20_runner`;
  - `validation_corpus`.
- **Banderas temporales:**
  - `POCUS_DRAFT_PENDING_FACULTY_REVIEW` (TD-04);
  - `MRS_AI_LANGUAGE`, `MRS_AI_REASONING` y `MRS_AI_CUES`, apagadas por
    defecto;
  - `TRANSITION_OBJECTIVES`, con su condición de retiro escrita.
- **No se eliminó nada.**

## 12. Otros ítems de la extensión

Negative evidence (59AJ), denominador (59AK), costo de IA (59N), desempeño
(59M), calidad de pruebas (59R), afirmaciones científicas (59AR), mapa de
investigación (59AS), privacidad, bitácoras y observabilidad (59AN–59AP),
exportación, linaje y portabilidad (59BF–59BH), y carga docente y del
residente (59BL, 59BM): ver el anexo de este documento.

## 13. Release readiness (59AQ)

**¿Qué impediría hoy usarlo en un piloto real de residencia?**

| Clase | Área | Qué | Referencia |
|---|---|---|---|
| **BLOCKER** para usar el Trace como evidencia evaluativa | Fidelidad del Trace | Las clases CRITICAL del lector: una orden de primera línea escrita de forma común se pierde o se archiva como plan, y el Trace atribuye la omisión al residente | `AUDITORIA_TRACE_CICLO5.md` |
| **BLOCKER** ídem | Estado de validación | La fidelidad del lector con texto de médicos externos no está medida. El piloto v1 está listo, no enviado | DF-15 |
| HIGH | Confiabilidad de la página | «Urgent intervention executed» sin ejecución; preguntas atadas a órdenes mal leídas | 59O-03, 59O-06 |
| HIGH | Consistencia clínica | `acs_54m_inferior` (VD) y el POCUS de las oclusiones | DF-20, sección 9 |
| HIGH | Flujo docente | Con la transición, cada encuentro deja 6 a 8 objetivos por valorar, unas 40–55 entradas | borrador TD/F/C |
| MEDIUM | Integridad longitudinal | Temas de historia vivos (L-F01); cronología del perfil (L-F04) | sección 2 |
| MEDIUM | Confiabilidad | Las auditorías corrieron en SQLite. El comportamiento en PostgreSQL se infiere del código | sección 1 |
| MEDIUM | Privacidad | `get_progress` con token de residente trae la evidencia esperada del caso (no se muestra) | I-F25 |
| MEDIUM | Escala | Cola docente lineal: 3 s con 1000 encuentros pendientes | sección 3 |
| LOW | Integridad | I-F02, I-F06, I-F09, I-F18, L-F06 | secciones 1 y 2 |
| LOW | Reproducibilidad | Empates de segundo y desfase de reloj | L-F02, L-F03 |

**Si el uso es sólo formativo, sin decisiones evaluativas,** los dos BLOCKER
bajan a HIGH, no a menos: el resumen de cada turno muestra qué acciones
corrieron, pero una pérdida silenciosa no se anuncia.

## 14. Qué no se hizo y por qué (59U, 59V)

- **No se corrigió ningún hallazgo del lector ni del Trace** (59I). Tampoco se
  tocaron puntajes, radar, eventos críticos, mappings ni datos clínicos
  (59BT).
- **No se hizo *chaos testing*** (59AG) **ni se corrió PostgreSQL.**
- **Se detuvo la extensión** cuando el trabajo que quedaba pedía decisiones
  suyas: DF-20, TDFC-1 a 8, y las decisiones de este documento.

---

## Anexo: secciones de la sesión principal

### Evidencia negativa (59AJ)

¿Distingue el sistema «sin datos» de «mal desempeño»?

| Categoría | ¿Existe hoy? | Dónde | ¿Se pierde la distinción? |
|---|---|---|---|
| **NOT OBSERVED** | Sí | objetivo sin observaciones: `status = not_observed` | No |
| **NOT EVALUABLE** (dominio) | Sí | dominio «no evaluable» en la rúbrica: fuera del promedio y del total comparable | No |
| **OPPORTUNITY ABSENT** | Sí | declaración NO: la valoración se rechaza y el objetivo no aparece pendiente | **En parte.** No queda registro por encuentro de que la oportunidad faltó; el progreso no puede decir «ofrecido en 3 de 10» |
| **OPPORTUNITY PRESENT BUT NOT DEMONSTRATED** | **No** | — | **Sí.** El docente sólo puede no valorar (se confunde con «pendiente») o marcar «Needs improvement» (se confunde con desempeño insuficiente). Es DF-17 (*faculty override*), diferido |
| **DEMONSTRATED INSUFFICIENT PERFORMANCE** | Sí | observación con `satisfactory = 0` («Needs improvement»): no suma, y se muestra aparte | No |
| **CONFIRMED FAILURE / SCORE 0** | Sí | dominio 0 confirmado; evento crítico confirmado (−3) | No |

**Decisión que se necesitará (DF-17):** cómo registrar que una oportunidad
declarada no ocurrió, sin que cuente como mal desempeño.

### Qué significa «C14 3/50» (59AK)

| Parte | Qué es |
|---|---|
| **3** | Observaciones de C14 **satisfactorias, no anuladas**, que cumplen la autonomía exigida (C14 no exige ninguna). Una por encuentro como máximo: índice único parcial |
| **50** | La meta vigente en `mrs_progress_targets`. Parte del **número de observaciones que pide la EPA C14 del Royal College** (EPA Guide 2018, p. 36) |
| **Origen de 50** | Es un número del marco, pero usado como **meta pedagógica local**: el docente puede cambiarla (`set_target`, con razón y revisión) |
| **Qué no es** | No es un requisito cumplido del marco. La guía exige contexto clínico real y varios observadores, y el simulador no reproduce eso (`target_source` en `objectives.py`) |

- **Las oportunidades NO** no cambian ni el 3 ni el 50: el denominador es una
  meta fija, no las oportunidades ofrecidas.
- **Varias observaciones del mismo encuentro** no pueden alterarlo: hay una por
  encuentro y objetivo.
- **«Needs improvement»** no suma al 3; se muestra aparte.
- **Riesgo de lectura:** «3/50» puede leerse como «6 % de competencia» o como
  avance de la EPA. **Recomendación:** que la pantalla diga «meta local de
  observaciones simuladas» junto al número. Es texto, no método.

### Costo de IA (59N)

Ninguna llamada de IA está en el lector de órdenes ni en el motor clínico:
leer, ejecutar y evaluar la traza es determinista.

| Función | Disparador | Modelo (default del código) | ¿Síncrona? | ¿Ruta clínica crítica? | Cache / reuso | Valor | Alternativa determinista | Recomendación |
|---|---|---|---|---|---|---|---|---|
| Generación de casos (`encounter_generator`, `generated_case`) | iniciar un encuentro con caso generado | `OPENAI_MODEL` (gpt-5-mini) + revisor opcional | Sí, antes de empezar | Antes del encuentro | No (cada caso es nuevo); fallas guardadas | Variedad | Banco (31) y catálogos | Para el piloto, banco o catálogo |
| Imágenes (`clinical_scene`, `image_broker`, `image_consistency`, `patient_appearance`, `scene_repair`) | foto de llegada y cambios de apariencia | `MRS_IMAGE_MODEL` (gpt-image-1.5) + revisor gpt-5-mini | Sí, al preparar | Al llegar | **Sí**: banco de imágenes con asignaciones, presupuesto y reserva por pedido | Realismo | Sólo el banco aprobado | Ya presupuestado; congelar al banco en pilotos |
| Conversación con el paciente (`patient_conversation`) | una pregunta de historia fuera de la ruta local | gpt-5-mini | Sí | **Sí**, durante el encuentro | Ruta local para preguntas comunes | Historia natural | Ampliar la ruta local | Medir cuántas preguntas llegan al modelo |
| Normalización de idioma (`ai_interpreter`) | antes de cada orden, si `MRS_AI_LANGUAGE` está activo | `OPENAI_MODEL` | Sí | Sí | No; presupuesto de llamadas por encuentro | Bajo: el lector entiende español | El lector determinista (por defecto) | **Apagada por defecto** (decisión B4) |
| Segundo lector de razonamiento (`reasoning_recognition`) | sólo cuando una orden se iba a retener, si `MRS_AI_REASONING` está activo | `OPENAI_MODEL` | Sí | Sí | No | Evita algunas retenciones | Captura determinista del razonamiento | Apagado por defecto; medir antes de encenderlo |
| Pistas de IA (`MRS_AI_CUES`) | con el segundo lector (`held`) o en cada decisión (`always`) | ídem | Sí | No se muestran al residente | No | Bajo | Patrones deterministas | Apagadas por defecto |
| Brief docente (`faculty_analysis`, prompt 1.6) | el docente lo pide | `OPENAI_MODEL` (gpt-5.6-luna en el portal) | Sí, en la página docente | No | **Sí**: `mrs_faculty_briefs`, ligado a la huella del encuentro | Ahorra lectura | La lista determinista de evidencia (`evidence_items`) | Mantener; nunca cuenta como evidencia |
| Propuesta de rúbrica (`rubric_analysis`, prompt 1.2) | el docente la pide | `OPENAI_MODEL` | Sí | No | **Sí**: `mrs_rubric_proposals`, ligada a la huella | Ahorra tiempo docente | El docente puntúa a mano | Mantener; medir cuánto la cambia el docente |
| Síntesis del Management Trace (`management_trace_analysis`, prompt 1.1) | se pide el informe del residente | `OPENAI_MODEL` | Sí | No | **Sí**: `mrs_learner_trace_analyses`, por huella | Retroalimentación | El Trace sin síntesis | Mantener |
| Traducción de prosa (`prose_translation`, prompt prose-es-1) | un lector en español ve prosa del modelo | `MRS_TRANSLATION_MODEL` | Sí | No | **Sí**: `mrs_prose_translations`, una vez por texto | Idioma | — | Mantener |
| Validation corpus | — | ninguno | — | — | — | — | — | Sin IA, por diseño |

**Oportunidades de costo sin bajar calidad:**

- **Medir antes de cambiar.** No hay un registro agregado del costo por
  función fuera del de imágenes. Se propone contar llamadas por función en la
  bitácora existente.
- **Conversación con el paciente.** Es la única IA encendida por defecto dentro
  del encuentro. Ampliar la ruta local con las preguntas que más llegan al
  modelo es el ahorro más directo.

### Desempeño (59M)

Mediciones livianas, mediana de 5 pasadas, con la máquina ocupada:

| Operación | Tiempo | Comentario |
|---|---|---|
| Lectura de una orden (`parse_family_actions`) | 0,55 ms | sin cambio por KD-01 |
| Extracción del razonamiento | 4,1 ms | igual al ciclo 4, dentro del ruido |
| Resolver la oportunidad de un objetivo | 0,13 ms | |
| Resolver las 19 de un encuentro, leyendo la base una vez (`summary`) | 0,21 ms | |
| Resolverlas objetivo por objetivo, como `pending_reviews` y `supported_objectives` | **2,96 ms** | 14 veces más: cada llamada vuelve a leer y a verificar la huella de la base |
| Congelar la base de un caso | 0,15 ms | |

La prueba de escala (sección 3) confirma el hallazgo con volumen: es la TD-09.

### Calidad de las pruebas (59R)

| Hallazgo | Severidad | Detalle | Acción |
|---|---|---|---|
| Módulos globales mutados al importar | MEDIUM | `test_generation_reload.py` cambia versiones y funciones de módulos al ser importado por pytest, y depende de un `reload` para restaurarlos. Pasa en las corridas completas, pero una falla del `reload` contaminaría al resto del shard | Documentado. Convertirlo en script de subproceso o envolverlo en `monkeypatch` cuando se toque |
| Fugas de entorno | — | Ninguna prueba escribe `os.environ` directamente; las del ciclo 4 y las nuevas usan `monkeypatch` (C-2026-09-26-20). La herramienta `play()` sí lo fija, como corresponde a un comando, y las pruebas la envuelven | Sin acción |
| Pruebas atadas a frases exactas | LOW | Muchas pruebas del lector comparan el texto exacto de un mensaje al residente. Es deliberado (el mensaje es comportamiento), pero encarece cambiar la redacción | Sin acción |
| Frases de prueba reutilizadas como anotación | — | La prueba de readiness usa sólo frases que ya existían en las pruebas y una anotación de prueba, marcadas como tales | Sin acción |
| Una prueba de migración no prueba lo que dice | LOW | «without losing rows» no inserta ninguna fila (I-F17) | Agregar una fila cuando se toque |
| Documentos generados que se desactualizan | Operacional | El catálogo publicado de hipoglicemia lista todas las correcciones: registrar una exige regenerarlo. Pasó dos veces en este ciclo, y la suite completa lo detectó ambas veces | Regenerarlo junto con cada corrección |
| Corridas completas que llenan el disco | Operacional | Cada corrida en 4 shards deja varios GB de `basetemp`. Restos de sesiones anteriores llenaron el disco temporal durante la segunda corrida del ciclo, que se descartó y se repitió | Borrar los `basetemp` al terminar cada corrida |
| Semillas | — | Las pruebas de trayectorias con azar fijan su semilla (p. ej. `test_working_model_recognition.py`, semillas 17 y 83) | Sin acción |

### Afirmaciones científicas (59AR)

La documentación es conservadora:

- ningún documento afirma que el sistema mida competencia, prediga desempeño,
  sea una evaluación estandarizada o sea comparable entre programas;
- el README dice explícitamente que no certifica EPAs ni infiere sesgos.

| Afirmación | Dónde | Clase | Recomendación |
|---|---|---|---|
| «validated trajectory» (PS001, PS002) | `README.md` (5 lugares), `INSTRUCCIONES_DE_PRUEBA.md` | **PLAUSIBLE BUT UNVALIDATED** como lenguaje: significa «probada por pruebas deterministas», no validación clínica | En textos nuevos, «tested» o «verificada»; no reescribir notas de versión históricas |
| «validada y renderizada» | `DEMO_RESEARCH_2026-09-23.md` | Validación de esquema, no clínica | Ídem |
| «Automated checking is not expert clinical validation» | `README.md` | SUPPORTED NOW | — |
| Metas de observaciones de las EPAs | `objectives.py`, `OBJECTIVE_TRACKING.md` | SUPPORTED NOW: el texto ya dice que alcanzar la meta no satisface la EPA | — |

### Qué evidencia falta para cada afirmación futura (59AS)

| Afirmación futura | Evidencia actual | Falta | Próximo estudio posible |
|---|---|---|---|
| Fidelidad del lector y del Trace | corpus de ensayo (autores internos), pruebas por clase, auditoría adversarial interna (90 frases) | lectura de texto libre de médicos externos | **el piloto de validación v1 (listo)** |
| Usabilidad | juego interno, tanda de 20 escenarios, 6 guiones de página | usuarios reales, tiempos, abandono | piloto con residentes y registro de fricción |
| Confiabilidad entre evaluadores | ninguna | dos docentes sobre los mismos encuentros | doble valoración de 20–30 encuentros |
| Confiabilidad de la rúbrica | reproducibilidad de la propuesta de IA (`docs/REPRODUCIBILIDAD_PUNTAJE.md`) | acuerdo docente-docente y test-retest | igual que la anterior, con la rúbrica en español |
| Validez de constructo | mapeos verificados contra las fuentes | relación con otras medidas del mismo constructo | comparación con evaluaciones de desempeño existentes |
| Sensibilidad longitudinal | arquitectura longitudinal probada con datos sintéticos (oráculo y escala de esta noche) | trayectorias reales | seguimiento de una cohorte durante meses |
| Comparabilidad entre programas | ninguna | datos de más de un programa | colaboración multicéntrica, después de lo anterior |
| Relación con desempeño externo | ninguna | medidas externas (OSCE, evaluaciones de rotación) | estudio correlacional, al final |

### Privacidad, bitácoras y observabilidad (59AN–59AP, acotado)

- **Identificadores.**
  - Los participantes del piloto son códigos (EM01…).
  - La ingesta lee sólo el cuerpo del DOCX: nunca propiedades, revisiones ni
    comentarios, que pueden traer el nombre del autor.
  - La llave código ↔ persona queda fuera del repositorio.
- **Nombre del revisor en los datos.** El nombre del docente está en la
  metadata C14 del banco y se copia a la base congelada de cada encuentro nuevo
  y a la procedencia de sus observaciones. Fue pedido explícitamente. Si esos
  datos se exportan, el nombre viaja con ellos.
- **Lo que el residente puede pedir a la API** incluye la evidencia esperada del
  caso (I-F25); no se muestra hoy.
- **Errores sin registro.** Todo error de base se muestra como «temporalmente
  no disponible» y no queda en ninguna bitácora (I-F10).
- **«El residente escribió X y el sistema hizo Y»: se puede reconstruir.** El
  Management Trace guarda el texto, la interpretación, el estado de ejecución y
  el resumen de cada turno; el encuentro guarda el commit con que se inició.
- **El hueco de observabilidad es menor.** No hay versión del lector por turno:
  si el despliegue cambia en medio de un encuentro, los turnos siguientes los
  lee otro código y el encuentro sigue mostrando el commit inicial.
  **Recomendación mínima:** guardar el commit en cada turno del Trace; es un
  campo corto.

### Exportación por marco, linaje y portabilidad (59BF, 59BG, 59BH)

**Hallazgo (MEDIUM, TD-03).** Los vínculos de marco de una observación no
siempre quedan congelados con ella:

- **Los 8 objetivos de Decision Challenge** (R1-05, R1-06, R1-07, R2-02 a
  R2-05, R3-01) tienen entre 4 y 6 vínculos ACGME o Royal College cada uno.
  Ninguno trae una contribución clasificada (DIRECT/PARTIAL). Por eso
  `provenance_json.contributions` queda vacío al confirmar, y sólo se congela
  `mapping_version`.
- **Sólo R1-03, R1-04 y R2-01** congelan sus contribuciones.
- **Los objetivos fundacionales** (TD1, F1, C1, C3, C4, C14) no tienen
  vínculos: el objetivo es la EPA misma.

**Consecuencia:** exportar «por hito» una observación de R2-02 exige leer los
vínculos **actuales** del objetivo. Si el mapping cambia, la evidencia antigua
se leería con los vínculos nuevos, salvo que se reconstruya la versión desde
git.

| Consulta | ¿Hoy? | Falta | Recomendación |
|---|---|---|---|
| POR MARCO (ACGME / Royal College) | **Parcial** | vínculos congelados para los 8 Decision Challenges | copiar a la procedencia todos los vínculos del objetivo, no sólo los clasificados |
| POR HITO / EPA | **Parcial** | ídem; los fundacionales sí, por su identificador | ídem |
| POR COMPONENTE | **Parcial** | el componente es texto (`component_observed`, `observable_component`) | un identificador de componente, cuando se decida |
| POR RESIDENTE | Sí | — | — |
| POR RANGO DE FECHAS | Sí | `created_at` en segundos de época | — |
| SÓLO OBSERVACIONES CONFIRMADAS | Sí | satisfactorias, no anuladas, y la confirmación del objetivo aparte | — |

**Linaje: ¿se puede llegar de la evidencia a la decisión clínica original?**
Sí, hoy, para cualquier observación:

1. observación: `evidence_json`, con las referencias `trace:N`;
2. encuentro: `attempt_id`, con `source_revision` y `payload_sha` del
   momento;
3. entrada exacta del Management Trace: el índice crudo;
4. caso: la base congelada, con su huella.

El eslabón débil es el primero de arriba, **meta del marco → componente**, por
el hallazgo anterior.

**Portabilidad.** Cada unidad conserva:

- procedencia de la oportunidad;
- contexto;
- evaluador;
- fecha;
- caso y versión: huella y commit.

**Le falta**, para ser interpretable sin la aplicación, el vínculo de marco
congelado de los Decision Challenges y la definición del objetivo en el
momento. Hoy sólo se guarda su identificador y la versión del mapping.

### Carga del docente y del residente (59BL, 59BM)

#### Docente, por encuentro (conteo estático del flujo actual)

| Paso | Qué hace | Entradas |
|---|---|---|
| 1 · Revisar el encuentro | abrir el encuentro y leer la evidencia (`Read the recorded evidence`) | 1 |
| 2 · Revisar el Management Trace | leer; el brief de IA es opcional y se pide aparte | 0–1 |
| 3 · Confirmar o rechazar observaciones | **por objetivo**: decisión, profundidad, autonomía, contexto, evidencia, notas y enviar | **7 por objetivo** |
| 4 · Revisar la rúbrica | **por dominio**: puntaje y razón (5 × 2), más un veredicto por evento crítico, y confirmar | unas 12–15 |
| 5 · Cerrar | confirmar un objetivo logrado es otra acción, en otra pantalla | 1 por objetivo |

- **La fricción mayor es el paso 3 multiplicado por los objetivos elegibles.**
  - Con la regla de transición, cada encuentro deja pendientes TD1, F1, C1, C3
    y C4, más C14 donde es YES, más su Decision Challenge: 6 a 8 objetivos.
  - Valorarlos todos son unas 40–55 entradas por encuentro, además de la
    rúbrica.
- **Mejoras de bajo costo:**
  - **Revisar las oportunidades TD/F/C.** Es la que más reduce: la cola deja de
    listar objetivos que el caso no ofrece, como ya pasó con C14 en 16 casos.
    Con el borrador de esta noche (`tdfc/`), serían 60 combinaciones NO menos.
  - **La carga del borrador de IA en el formulario ya existe;** medir si el
    docente la usa.
  - **La evidencia citada** suele ser la misma en varios objetivos. Proponerla
    una vez sería un cambio de UX: se documenta, no se hace.

#### Residente, por encuentro (corpus de ensayo: 20 guiones × 2 idiomas)

| Medida | Por encuentro | Comentario |
|---|---|---|
| Órdenes escritas | 4,8 | evidencia útil |
| Respuestas a aclaraciones | ~1 | fricción: 19 de 115 pasos (17 %), todas previstas por los guiones (p. ej. oxígeno sin flujo, KB-01) |
| Categorías de razonamiento declaradas | ~10,6 | evidencia útil: 212 en 20 encuentros |
| Modelos de trabajo declarados | ~1,5 | evidencia útil |
| Reflexión y plan al cerrar | ~12 campos | evidencia de los Decision Challenges, pero es la carga más grande |

- **Casi todo lo que escribe el residente produce evidencia.**
- **La fricción del sistema es la aclaración.** En estos guiones es de una por
  encuentro, y ninguna fue imprevista. La auditoría del Trace muestra que con
  otras formas de escribir la fricción sube (sección 6).
- **El costo mayor es la reflexión final**: unos 12 campos frente a unas 5
  órdenes. Si el piloto con residentes lo confirma, **la decisión es
  pedagógica, no técnica**: qué campos de reflexión son necesarios para cada
  desafío.
