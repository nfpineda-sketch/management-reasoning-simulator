# Imágenes del paciente: banco persistente, misma persona, estado actual

Trabajo autorizado el 2026-09-26: mantener imágenes estáticas y mejorar su generación, persistencia,
reutilización y evolución con el paciente. Sin video, GIF ni animación. El consumo está en
`docs/IMAGENES_REGISTRO.md`; las decisiones que te tocan, en `docs/IMAGENES_DECISIONES_CLINICAS.md`.

## En una frase

La foto del paciente pasó de vivir en la memoria de una pestaña a vivir en la base de la app:

- la misma persona sintética durante todo el encuentro, al recargar, al reanudar y tras un reinicio;
- cada estado es una edición de una sola fotografía de esa persona;
- nunca se muestra una foto de un estado anterior como si fuera el actual;
- cada solicitud pagada se reserva contra un tope antes de salir;
- queda registrado qué mostró la sala en cada encuentro.

## 1. Diagnóstico del circuito anterior (con evidencia)

| Causa | Evidencia | Corrección |
|---|---|---|
| **Nada se guardaba.** La foto vivía en la sesión del navegador (máximo 8 por sesión). Una recarga, una reanudación en otra pestaña o un reinicio del servidor pagaban una foto nueva, **de otra persona**. | Código (`scene_jobs.SceneJobs`, `clinical_scene.scene_image`). Sin URL que venza: la foto llegaba en base64, pero no se guardaba en ninguna parte. | Banco persistente en la base de cuentas (`image_bank`); identidad asignada al encuentro y guardada con él. |
| **2,6 MB por cada orden.** El PNG del proveedor (mediana 1,98 MB, n = 26) viajaba en base64 dentro del mismo HTML que el monitor. Cada cambio del monitor reenviaba la foto completa. | Medido con Chromium real contra Streamlit 1.64: **2.638.596 bytes por orden** (n = 4). | La foto va en un elemento propio, como WebP (mediana 67 KB, n = 26): **20.343 bytes por orden** (n = 4), y la carga inicial pasa de 2,64 MB a 104 KB. |
| **La sala ignoraba la regla B1.** El lanzamiento retiene la clave de la imagen a un rol sin permiso de gasto y a un caso en revisión, pero la sala leía la clave directamente y generaba igual. | Prueba: con `MRS_PAID_GENERATION=admin`, un residente provocaba la generación. | La sala sigue la misma regla, en los dos caminos (C-2026-09-26-05). |
| **Demanda sin reutilización.** En los 20 guiones de la tanda, ensayados sin red por la página real, el diseño anterior pidió **51 imágenes** (20 creaciones y 31 ediciones), más revisiones y correcciones, **sin recargar nunca**. Hay 43 estados visuales distintos. | `scratchpad/image_demand.py`: 139 pasos, 0 detenidos. Lo que más cambia entre pasos es el esfuerzo respiratorio (17 cambios), la expresión (14), el soporte (9) y la conciencia (9). | La foto se pide una vez por persona y estado, para siempre. Volver a un estado ya visto no cuesta nada. |
| **Respuestas tardías.** Dentro de una sesión ya se guardaban bajo su propio estado y no se mostraban fuera de él. Al cambiar de encuentro se descartaban: se pagaban y se perdían. | Código (`SceneJobs.discard`). | Toda respuesta se guarda en el banco bajo su persona y su estado. Sólo se muestra si coincide con el estado actual. |
| **Reintentos.** No había reintentos automáticos del SDK (`max_retries=0`), pero **recargar era un reintento pagado**. | Código. | Reintento según el tipo de falla (§4), con pausa por estado fallido, compartida entre sesiones y procesos. |

Lo que ya estaba bien y se conservó: la espera nunca bloqueó órdenes ni el reloj clínico (trabajos en
segundo plano); ninguna foto de un estado anterior se rotulaba como actual; la revisión automática de
coherencia y su única corrección. Ninguna comprobación se relajó.

## 2. Qué se construyó

| Pieza | Qué hace |
|---|---|
| `image_identities` | 30 personas sintéticas: 5 bandas de edad × 2 sexos × 3 tonos de piel. Cada tono aparece 5 veces, y contextura y pelo varían con independencia del tono. Sólo descriptores visuales, sin categorías raciales ni rasgos de conducta, higiene, pobreza o consumo. Todas con la misma bata, la misma sala y la misma manta. Cada caso de autor tiene al menos 3 compatibles. |
| `image_selection` | Primero la compatibilidad (edad y sexo del caso; nunca se cambia el caso). Después la novedad para ese residente (lo no visto; si todo se vio, lo visto hace más tiempo, registrado como `bank_limited`). Después lo ya guardado (sin espera ni costo). Después el equilibrio entre familias y en total. El desempate es reproducible. |
| `image_bank` | Tablas nuevas: imágenes deduplicadas por contenido; activos con estado, dispositivos, modelo, versiones, referencia usada y revisión automática; revisión visual y clínica (sólo personas, con historial); exclusión con motivo; asignación de persona por encuentro; registro de lo mostrado; trabajos; presupuestos; registro de gasto. |
| `image_broker` | Una solicitud por persona y estado, en el proceso y entre procesos (reclamo con plazo, que vence si el proceso muere). Primero el ancla de la persona, como trabajo propio. El peor caso se reserva antes de enviar. La única corrección se mantiene. Lo que la revisión no alcanzó a juzgar se guarda y se revisa de nuevo sin pagar otra imagen. |
| `image_pricing` | Tarifa verificada, cotas por solicitud y cálculo del costo con el uso informado por el proveedor. |
| `image_scene` | La sala con el banco: la persona del encuentro, la foto del estado actual o la vista neutral con su motivo, y el registro de cada cambio de lo mostrado. `MRS_IMAGE_BANK=off` vuelve al camino anterior. |
| `image_pack` | El banco como paquete versionado en la rama (`assets/patient_images/`). La app lo importa a su base al arrancar, una vez, sin sobrescribir nada. |
| `image_bank_portal` | Panel docente («Patient image bank (faculty)») y registro de lo mostrado en la revisión de cada encuentro. |
| `tools_image_bank.py` | Plan, lotes pagados, inventario, registro de gasto, exportación e importación, retiro con motivo. |

**Identidad, estado y soporte, separados.** La identidad es la persona del banco. El estado observable
y el soporte salen del contrato visual que ya existía (`patient_appearance.appearance_state`): la
conciencia, la expresión, la piel, el sudor, el moteado y el esfuerzo respiratorio vienen del motor, y
el soporte sale de los tratamientos **ejecutados**. No hay un segundo modelo fisiológico. Una orden
retenida, cancelada o no ejecutada no cambia `treatments`, así que no pone un dispositivo, y retirar el
oxígeno lo quita (probado con la orden real «Retiro el oxígeno»). La clave de estado incluye todo el
contrato, dispositivos incluidos: una foto sólo se muestra para exactamente el estado que representa.

## 3. Inventario

| | Cantidad | Detalle |
|---|---|---|
| Imágenes de paciente existentes antes de hoy | **0 recuperables** | El diseño anterior no guardaba ninguna. La única registrada (`patient_scene.png` de la demo del 2026-09-22) está en `local-data/` de tu computador, no en la rama ni en este entorno. Si la quieres en el banco, se importa con `tools_image_bank.py import`, como caso de otra configuración. |
| Nuevas, **utilizables** | **7** | V22: ancla, somnoliento, obnubilado, recuperado. V18: ancla. V11: ancla y somnolienta. Todas **pendientes de revisión visual y clínica**. |
| Nuevas, **rechazadas o retiradas** (con motivo, fuera de la selección) | **19** | 10 del estado con mascarilla (el revisor no reconoce la mascarilla de reservorio). 4 del sudor marcado de V18 (el sudor no aparece sobre piel oscura). 2 primeras anclas de V22 más su estado (bolsas de suero junto a la cama). Primera ancla de V11 más su estado (cánula en la muñeca). |
| **Faltantes** para hipoglicemia | 7 estados × personas | Los 7 estados que produce la familia (tabla en `image_pilot.py`), más cualquier dispositivo que el residente ordene. Con la persona ya elegida, cada estado nuevo cuesta una edición (~US$0,07 más su revisión). |

## 4. Reintentos, pausas y presupuesto

| Falla | Qué pasa |
|---|---|
| Proveedor ocupado, caído o inalcanzable | Un reintento tras una pausa, reservado de nuevo; si el presupuesto no lo cubre, queda la falla. |
| Tiempo agotado | Sin reintento: puede haberse procesado y cobrado. Queda cobrado por su reserva. |
| Rechazo, cuota, autenticación, modelo, formato | Sin reintento. |
| Desajuste definido en la revisión | Una corrección; si vuelve a fallar, se detiene. |
| La revisión no alcanzó veredicto | La imagen se guarda sin revisar y se revisa de nuevo la próxima vez, sin pagar otra. |
| Pausa antes de pedir otra vez automáticamente el mismo estado | 10 a 15 min para fallas transitorias; 6 h si la revisión no alcanzó veredicto; 24 h para desajustes y rechazos. Una persona puede pedirlo antes con «Retry patient image», y paga otra vez. |

El presupuesto vive en la base: `imagenes-2026-09-26`, US$10 y 30 solicitudes, sin reinicio. Un modelo
sin tarifa verificada (por ejemplo `gpt-image-2`) no se usa. Agotado el presupuesto, la sala sigue
mostrando lo guardado y dice por qué no hay foto nueva. Una nueva autorización se configura con
`MRS_IMAGE_BUDGET_ID`, `MRS_IMAGE_BUDGET_USD` y `MRS_IMAGE_BUDGET_REQUESTS`, con otro identificador.

## 5. Verificación (tu lista, punto por punto)

**R** = con imágenes reales del proveedor; **S** = con respuestas simuladas y el motor real.

| # | Verificación | Cómo | Resultado |
|---|---|---|---|
| 1 | Inicio con imagen compatible disponible | **R**: el paquete del piloto en una base nueva; el caso de 54 años muestra la foto de V22 sin ninguna llamada. **S**: un segundo residente. | Pasa |
| 2 | Cambio de estado manteniendo identidad | **R**: V22 en 4 estados, V11 en 2, siempre editados desde su ancla; la continuidad la juzgué mirando cada imagen. **S**: glucosa y reevaluación con el motor. | Pasa |
| 3 | Aparición y retirada de dispositivos | **S**: la orden real de oxígeno pone la mascarilla, «Retiro el oxígeno» la quita, y una orden retenida no pone nada. **R**: el estado con mascarilla no pasó la revisión automática (10 candidatos) y queda en la vista neutral. | Pasa lo técnico. **La imagen real con mascarilla no se logró.** |
| 4 | Cambio de estado con una solicitud en curso | **S** | Nunca se muestra el estado anterior |
| 5 | Falla y respuesta tardía | **S**, con fallas simuladas del proveedor y de la revisión | La respuesta tardía se guarda bajo su estado y no se muestra en otro |
| 6 | Recarga y reanudación | **S**; **R** con la importación del paquete | Misma persona, sin llamadas |
| 7 | Reinicio del servicio | **S**, en SQLite y en Postgres 16 local | Misma persona y mismo presupuesto |
| 8 | Sin mezcla entre usuarios y encuentros | **S** | Nadie lee ni escribe el registro de otro encuentro |
| 9 | Reutilización sin llamadas | **S** y **R** | 0 llamadas |
| 10 | Selección por compatibilidad y exposición | **S** | Lo no visto primero; `bank_limited` cuando todo se vio |
| 11 | Presupuesto y tope de solicitudes | **R**: 26 de 30, US$2,50. **S**: reservas concurrentes en Postgres (8 hilos, exactamente 3 aceptadas). | Pasa. Hubo un error de mi herramienta: 8 solicitudes en intentos equivalentes, ya corregido y probado. |

Pruebas nuevas, 64 en total: `test_the_image_bank.py` (33), `test_the_image_bank_on_postgres.py` (4,
contra Postgres local), `test_the_room_shows_the_bank.py` (21), `test_image_bank_portal.py` (4) y
`test_tools_image_bank.py` (2).

## 6. Métricas medidas

| Métrica | Muestra | Valor |
|---|---|---|
| Bytes por orden que cambia el monitor | n = 4 por modo, Chromium y Streamlit 1.64 locales | antes 2.638.596 · ahora 20.343 |
| Carga inicial de la sala | 1 por modo | antes 2.637.858 · ahora 104.163 |
| Peso de la foto | 26 imágenes reales | PNG del proveedor: mediana 1.984.184 bytes · WebP del navegador: 67.199 |
| Latencia por llamada | 26 solicitudes y 26 revisiones | crear 8 s · editar 13 s · corregir 13 s · revisar 7 s (medianas) |
| Duración de un trabajo | 17 trabajos | mediana 24 s (13–57) |
| Aceptación a la primera | 17 trabajos | 10 guardados, 7 rechazados tras su corrección: todos de dos estados (mascarilla y sudor marcado) |
| Reutilización | pruebas S, y R con el paquete | recarga, reanudación, reinicio y segundo residente: 0 llamadas |
| Demanda del diseño anterior | 20 guiones, 139 pasos | 51 imágenes pagadas sin recargar; 43 estados distintos |

## 7. Limitaciones pendientes

- **El revisor automático no reconoce la mascarilla de reservorio** en estas fotos: 10 candidatos. A mi
  revisión, las últimas se ven correctas. No se relajó la revisión.
- **El sudor marcado no aparece sobre piel café oscura** (V18: 4 candidatos, 2 métodos). Queda la vista
  neutral para ese estado, y el sudor sigue en el examen escrito.
- **El generador agrega equipo de infusión en la sala** pese a la instrucción, y el revisor no lo detecta
  siempre. La revisión humana es necesaria antes de exponer a residentes.
- **Lo leve no se ve en una foto**: sudor leve, palidez leve, esfuerzo respiratorio leve. La sala lo dice
  en texto junto a la foto, como antes.
- **La calidad de la imagen no está resuelta por las pruebas simuladas**: sólo lo está el manejo técnico.
- **La app de desarrollo corre el código anterior hasta «Reboot app»**. Desde este entorno no se alcanza
  su base (el proxy no admite TCP a bases de datos), por eso el paquete.

## 8. Revisar el resultado en desarrollo

1. Reinicia la app de desarrollo («Reboot app»). Al primer uso crea sus tablas, importa el paquete (una
   vez) y continúa el mismo presupuesto: 26 de 30 solicitudes, US$2,50.
2. Entra como docente o administrador. En «Faculty sandbox», abre **«Patient image bank (faculty)»**.
   - Ves el presupuesto, las personas y sus fotos.
   - «Show rejected and excluded images too» muestra también las rechazadas, con su motivo.
   - Registra la **revisión visual** y la **clínica** con tu cuenta, o excluye con un motivo.
3. Para verlas en la sala, abre en el sandbox un encuentro de hipoglicemia con el caso de 54 años (R1-06
   o R1-07). Aparece V22.
4. En la revisión de cualquier encuentro, «Show the patient image record» muestra qué mostró la sala y
   cuándo.
5. **Aviso de gasto:** con el código nuevo, un encuentro en desarrollo que necesite una foto que no existe
   la pide, dentro del presupuesto. Quedan 4 solicitudes: se agotan pronto, y después la sala muestra lo
   guardado y la vista neutral. Para seguir generando hace falta una nueva autorización.
