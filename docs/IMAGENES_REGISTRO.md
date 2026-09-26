# Imágenes del paciente: registro de avance y de consumo

Registro persistente del trabajo autorizado el 2026-09-26. Se actualiza **antes** de cada lote pagado,
con lo que se reserva, y **después**, con lo que realmente pasó. Si el trabajo se interrumpe, se retoma
desde aquí sin reiniciar el presupuesto: lo reservado y no liquidado cuenta como gastado.

## Autorización

> Autorizo hasta US$10 y un máximo de 30 solicitudes pagadas de generación o edición de imágenes
> estáticas para este trabajo, lo que se alcance primero. Todos los reintentos cuentan dentro de ambos
> límites.

- Presupuesto en el código: `imagenes-2026-09-26`, US$10,00 y 30 solicitudes (`image_pricing.DEFAULT_BUDGET`).
- **Qué cuenta como solicitud:** cada creación, edición o corrección de una imagen, reintentos
  incluidos. La revisión automática de coherencia (`gpt-5-mini`) no es una generación ni una edición: no
  consume una de las 30, pero **su costo sí cuenta** en los US$10 y queda en el mismo registro.
- No incluye video, encuentros clínicos pagados ni otros servicios.

## Tarifa verificada

Consultada el 2026-09-26 en la página de precios de OpenAI
(`https://developers.openai.com/api/docs/pricing`), mediante una búsqueda restringida a
`developers.openai.com` y `openai.com`. La descarga directa de la página está bloqueada por la red de
este entorno.

| Modelo | Uso | Precio por millón de tokens | Estado |
|---|---|---|---|
| `gpt-image-1.5` | texto de entrada | US$5,00 | verificado |
| `gpt-image-1.5` | imagen de entrada | US$8,00 | verificado |
| `gpt-image-1.5` | imagen de salida | US$32,00 (US$0,013 por imagen baja 1536×1024) | verificado |
| `gpt-5-mini` | revisión de la imagen | se usa una **cota**: US$2,00 entrada, US$16,00 salida | **no verificado**: el resumen de la búsqueda se contradijo; la cota está por encima de todas las cifras vistas |

Configuración que usa la app: 1536×1024, calidad `low`, PNG, `input_fidelity` alta en las ediciones,
revisión con `max_output_tokens` 4096. Un modelo sin tarifa en `image_pricing.CEILINGS` no se usa: sin
cota no se puede garantizar el límite.

## Estimación conservadora por solicitud (lo que se reserva)

| Solicitud | Reserva | De dónde sale |
|---|---|---|
| Crear (`gpt-image-1.5`) | US$0,05 | 2.500 tokens de texto + 1.000 de imagen de salida ≈ US$0,045 |
| Editar desde el ancla | US$0,15 | + hasta 12.000 tokens de imagen de entrada ≈ US$0,141 |
| Corregir (dos imágenes de entrada) | US$0,25 | ≈ US$0,237 |
| Revisar (`gpt-5-mini`) | US$0,10 | 16.000 de entrada + 4.096 de salida a la cota ≈ US$0,098 |

Cada trabajo reserva **el peor caso completo** antes de enviar la primera llamada: la imagen, su revisión,
la única corrección y su revisión. Lo que no usa se devuelve al terminar. Un reintento se reserva de
nuevo. Una falla o un *timeout* **quedan cobrados por su reserva**: no se suponen gratis. El costo
calculado sale del uso que informa el proveedor, a la tarifa de arriba. Es un cálculo, no una factura:
la factura sólo está en la cuenta del proveedor.

## Acceso

- Hasta las 06:20 UTC la red del entorno denegaba `api.openai.com`.
- Desde tu configuración, el proxy del entorno agrega la credencial: la clave nunca está en este
  contenedor. Verificado con la lista de modelos, que no se cobra.
- Desde aquí no hay acceso a la base de desarrollo (Neon): el proxy no admite conexiones TCP a bases de
  datos. Por eso el piloto se guarda en una base local y viaja en la rama como paquete
  (`assets/patient_images/`), con sus imágenes, su procedencia y este registro de gasto. La app de
  desarrollo lo importa a su base al reiniciarse, una vez, sin sobrescribir nada.

## Plan del piloto (hipoglicemia)

Tres personas sintéticas, compatibles con los tres casos de la familia, con estados que el motor
realmente produce (`image_pilot.py`). Cada persona se dibuja primero en un estado neutro, su **ancla**, y
cada estado es una edición de esa misma fotografía.

| Lote | Persona | Caso | Estados | Peor caso |
|---|---|---|---|---|
| 1 | V22: hombre de unos 55, piel muy clara | `hypoglycemia_54m_thiamine` | ancla + somnoliento con sudor leve | US$1,10 · 4 solicitudes |
| 2 | V22 | ídem | obnubilado; obnubilado con mascarilla de reservorio; recuperado | US$1,80 · 6 solicitudes |
| 3 | V18: hombre de unos 28, piel café oscura; V11: mujer de unos 68, piel oliva clara | `hypoglycemia_28m`, `hypoglycemia_76f` | ancla + llegada + recuperado, cada uno | US$3,40 · 10 solicitudes |

Si un lote muestra un defecto repetido, se corrige el método antes del siguiente; no se gasta en
intentos equivalentes.

## Lotes

### Lote 1 (06:26–06:27 UTC)

- **Antes:** reserva máxima US$1,10 y 4 solicitudes de imagen. Gastado hasta aquí: US$0,00; 0 solicitudes.
- **Después:** 55 s. 6 llamadas enviadas, 0 reintentos, 0 fallas. **3 solicitudes de imagen** (crear el
  ancla, corregirla una vez, editar el estado) y 3 revisiones. **US$0,2142**, calculado con el uso que
  informó el proveedor (ninguna llamada quedó a estimación). Lo no usado de la reserva se devolvió.

  | # | Llamada | Reserva | Costo calculado |
  |---|---|---|---|
  | 1 | crear ancla | 0,0500 | 0,0224 |
  | 2 | revisar | 0,1000 | 0,0154 |
  | 3 | corregir ancla | 0,2500 | 0,0723 |
  | 4 | revisar | 0,1000 | 0,0130 |
  | 5 | editar: somnoliento con sudor leve | 0,1500 | 0,0723 |
  | 6 | revisar | 0,1000 | 0,0188 |

  El costo de las revisiones está calculado a la **cota**, no a la tarifa real de `gpt-5-mini`: el real
  es menor.

- **Revisión de las imágenes** (la hice mirando cada una, antes de ampliar):
  - **Identidad:** excelente. Mismo rostro, pelo, bata, sala, encuadre y monitores en el ancla y en el
    estado.
  - **Dispositivos:** en los dos candidatos de ancla hay bolsas de suero y líneas colgando junto a la
    cama. El revisor automático rechazó el primero («tratamiento activo no pedido») y aceptó el
    corregido porque no están conectadas, pero un residente podría leerlas como una infusión que nadie
    indicó.
  - **Estado:** el somnoliento es compatible pero débil. Los párpados están algo más pesados, pero la
    mirada sigue fija en la cámara. La palidez y el sudor leves no se ven: el revisor los marcó como
    limitaciones y la sala lo dice en texto.
- **Defecto repetido, método corregido antes de seguir** (`image_broker.PROMPT_VERSION = bank-1.1`):
  - la sala del banco se pide sin bolsas, atriles, líneas ni bombas;
  - cada estado de conciencia se pide reconocible a tamaño normal, en proporción, sin conservar la mirada
    abierta del ancla;
  - un estado sólo se usa si se editó desde el ancla vigente de esa persona.
  - El ancla anterior de V22 y su estado quedan **retirados, no borrados**, con el motivo.
- **Defecto de concurrencia encontrado en las pruebas y corregido:** dos estados de una persona sin ancla,
  pedidos a la vez, dibujaban dos anclas distintas. Ahora el ancla es un trabajo propio y único.

### Lote 1b (V22 de nuevo, con el método corregido; 06:35–06:36 UTC)

- **Antes:** reserva máxima US$1,10 (ancla y estado, cada uno con su corrección) y 4 solicitudes. Gastado
  hasta aquí: US$0,2142; 3 solicitudes.
- **Después:** 37 s. 4 llamadas, 0 reintentos, 0 fallas, 0 correcciones: **2 solicitudes** (ancla y
  estado). Acumulado: **US$0,3441** con uso informado por el proveedor; **5 de 30** solicitudes.
- **Revisión:** identidad igual de buena. El somnoliento ahora se reconoce a tamaño normal, en
  proporción: párpados a media altura, mirada que se va hacia abajo, boca entreabierta. La sala ya no
  tiene bolsas junto a la cama; queda equipo de pared (tomas de gases, tubos enrollados en la esquina),
  no conectado al paciente. El paciente quedó más a la izquierda de lo pedido (27 % en vez de 40 %), con
  la mitad derecha libre para el monitor.

### Lote 2 (V22: obnubilado, obnubilado con mascarilla, recuperado; 06:36–06:38 UTC)

- **Antes:** reserva máxima US$1,80 y 6 solicitudes. Gastado hasta aquí: US$0,3441; 5 solicitudes.
- **Después:** 8 llamadas, 0 reintentos. **4 solicitudes.** Acumulado: **US$0,7641** con uso informado;
  **9 de 30** solicitudes.
  - Obnubilado: aceptado a la primera (21 s), con limitaciones de sudor y palidez leves.
  - Recuperado: aceptado a la primera (15 s), con la limitación de palidez leve.
  - **Obnubilado con mascarilla de reservorio: rechazado dos veces** (la edición y su única corrección).
- **Por qué:** las dos imágenes muestran la mascarilla con su bolsa, bien puesta, pero **sin tubo de
  oxígeno**. Una mascarilla sin conexión no entrega oxígeno: como imagen de un soporte ejecutado es
  incoherente. El rechazo es defendible, aunque la explicación del revisor fue imprecisa («ninguna
  interfaz» y «tratamiento activo no pedido»). El texto de la sala ya pedía «oxygen tubing» y el modelo lo
  omitió dos veces.
- **Método corregido antes de reintentar** (`bank-1.2`): para cánula, mascarilla simple y de reservorio
  se pide el tubo visible hasta el flujómetro de la pared.

### Reintento del estado con mascarilla (forzado, contado; 06:39–06:42 UTC)

- **Antes:** reserva máxima US$0,60 y 2 solicitudes. Gastado hasta aquí: US$0,7641; 9 solicitudes.
- **Después: un error de mi herramienta.** El reintento hizo **4 intentos equivalentes, no 1**: **8
  solicitudes y US$0,9601**, 16 llamadas. El bucle que espera el ancla de una persona nueva forzaba de
  nuevo en cada vuelta, y un estado rechazado se volvía a pedir. Los límites se respetaron: cada trabajo
  reservó su peor caso antes de empezar. Pero es gasto que no debió ocurrir.
  - Corregido: `--force` vale sólo para la primera solicitud, y un rechazo corta el bucle.
  - Prueba nueva: `test_tools_image_bank.py`. Falla con el bucle anterior y pasa con el corregido.
- **Acumulado: US$1,7242 con uso informado; 17 de 30 solicitudes.**
- **Resultado:** los 4 intentos fueron rechazados igual que los del lote 2. A mi revisión, las imágenes
  nuevas se ven correctas: mascarilla con reservorio sobre nariz y boca, ojos cerrados, misma persona, y
  en varias se ve el tubo hacia la pared. Aun así el revisor automático (`gpt-5-mini`, razonamiento mínimo)
  clasifica el dispositivo como «otro tratamiento activo» o «mascarilla simple», nunca como mascarilla
  de reservorio: **10 candidatos, 5 trabajos, la misma clasificación**.
- **Decisión:**
  - No gasto más en ese estado.
  - No relajo la revisión para que pase.
  - Los candidatos quedan excluidos, con su motivo, visibles para tu revisión en el banco.
  - En un encuentro, ese estado muestra la vista neutral identificada, nunca una imagen equivocada.
  - Si una revisión humana debe poder aceptar una imagen que el revisor automático rechazó, es una
    decisión tuya: queda en `docs/IMAGENES_DECISIONES_CLINICAS.md`.

### Lote 3 (reducido: dos personas, llegada; verificar diversidad, no llenar inventario)

- V18 (hombre de unos 28, piel café oscura): ancla y somnoliento con sudor **marcado**. Es el caso donde
  el sudor y la palidez no deben apoyarse sólo en el color de la piel.
- V11 (mujer de unos 68, piel oliva clara): ancla y somnolienta con sudor leve.
- **Antes:** cuatro trabajos, uno tras otro. Peor caso de cada uno: US$0,50 el ancla y US$0,60 el estado,
  2 solicitudes cada uno. Gastado hasta aquí: US$1,7242; 17 solicitudes. Quedan 13.
- **Después (06:45–06:46 UTC):** 10 llamadas, 0 reintentos. **5 solicitudes.** Acumulado: **US$2,1275**;
  **22 de 30**.
  - V11: ancla y somnolienta aceptadas a la primera. La identidad se conserva y la somnolencia se
    reconoce.
  - **V18 somnoliento con sudor marcado: rechazado dos veces**, con razón: la piel se ve seca. El
    generador no dibujó el sudor marcado sobre piel café oscura.
- **Revisión:**
  - **El ancla de V11 trae una cánula venosa con su línea en la muñeca**, y su estado la heredó. No está
    en el contrato ni fue ejecutada. En hipoglicemia importa, porque el motor modela el acceso venoso.
    El revisor automático no la detectó. Ancla y estado quedan **retirados** con el motivo.
  - **El ancla de V18 tiene en la pared un set de infusión con su tubo hacia la cama.** Es la misma
    tendencia de las primeras anclas de V22: el generador agrega equipo de infusión pese a la
    instrucción, y el revisor automático no lo detecta de forma constante. Queda para tu revisión
    visual; no la retiro porque no está conectado al paciente.
- **Método corregido** (`bank-1.3`):
  - se prohíbe explícitamente cualquier cánula, catéter, apósito o tubo en brazos y manos;
  - el sudor marcado se pide como textura y brillo, visible en cualquier tono de piel, nunca como
    cambio de color.

### Intentos finales (con `bank-1.3`)

- V18 somnoliento con sudor marcado: un intento, forzado una sola vez. Peor caso US$0,60, 2 solicitudes.
- Después, si quedan al menos 4 solicitudes: V11 ancla y somnolienta. Peor caso US$1,10, 4 solicitudes.
- Gastado hasta aquí: US$2,1275; 22 solicitudes. Después de esto no se hacen más solicitudes esta noche.
- **V18 (06:50 UTC):** un solo trabajo, como corresponde: la edición, su corrección y dos revisiones.
  **2 solicitudes.** Acumulado: **US$2,3661; 24 de 30.** **Rechazado otra vez**, las dos imágenes por la
  misma razón: «sin gotas de sudor visibles; la piel se ve seca». A mi revisión también: la somnolencia
  se ve, la identidad se conserva, el sudor no aparece.
  - Son **4 candidatos en 2 trabajos**, con dos métodos distintos. Con este generador y esta configuración,
    el sudor marcado sobre piel café oscura no se logra.
  - No lo intento más. Queda como **limitación de representación**: en ese estado la sala muestra la
    vista neutral identificada, y el sudor sigue en el examen escrito.
  - No se sustituye por otra identidad de piel más clara: eso sería justamente asociar el hallazgo a un
    tono de piel.
- **V11 (06:52 UTC):** ancla y somnolienta con `bank-1.3`, aceptadas a la primera: **2 solicitudes**, 48 s.
  Acumulado: **US$2,4959; 26 de 30.** Brazos y manos sin cánula: la corrección funcionó. En la esquina
  del ancla volvieron a aparecer bolsas colgadas, que la edición del estado quitó. La instrucción sobre
  la sala no se cumple siempre, y el revisor automático no lo detecta siempre.

## Cierre del piloto (06:53 UTC)

**No se hacen más solicitudes pagadas esta noche.** Quedan 4 solicitudes y US$7,50 sin usar: no son una
meta.

| | |
|---|---|
| Solicitudes de imagen | **26 de 30**: 5 creaciones, 13 ediciones, 8 correcciones (corregido el 2026-09-26 con el registro del paquete; decía 11 y 10). 8 de ellas fueron el error de la herramienta. |
| Revisiones automáticas | 26 (no cuentan entre las 30; su costo sí cuenta) |
| Reintentos por falla del proveedor | 0 |
| Fallas o *timeouts* del proveedor | 0 |
| Gasto | **US$2,4959**, todo calculado con el uso informado por el proveedor, a la tarifa verificada para las imágenes y a la cota para las revisiones. La factura real está en tu cuenta de OpenAI. |
| Saldo | **US$7,5041 y 4 solicitudes** |

Imágenes utilizables:

- **V22:** ancla, somnoliento, obnubilado y recuperado.
- **V18:** ancla.
- **V11:** ancla y somnolienta.

Todas quedan **pendientes de revisión visual y clínica**: el revisor automático no es una aprobación.

Rechazadas o retiradas, con su motivo, fuera de la selección y visibles para tu revisión:

- las 10 del estado con mascarilla;
- las 4 del sudor marcado de V18;
- las primeras anclas de V22 y V11 y sus estados.

Todo viaja en `assets/patient_images/`: las imágenes, su procedencia, los 17 trabajos y las 72 filas de
este registro. La app lo importa a su base al arrancar, una vez, sin sobrescribir nada.

## Revisión tras el reinicio de la app de desarrollo (2026-09-26, tarde)

- **La app de desarrollo no se puede abrir desde este contenedor.** La página carga, pero el proxy del
  entorno no deja pasar el WebSocket que Streamlit necesita (`/_stcore/stream`: «Error during WebSocket
  handshake»). Sí responden `/_stcore/health` y `/_stcore/script-health-check` (`ok`): la app arrancó y
  su script corre sin error para una visita sin sesión. No es evidencia del panel ni de la sala.
- **Copia local, no la app de desarrollo:** el mismo commit y el mismo paquete, una base Postgres local
  nueva, una cuenta docente local de prueba, modo sin conexión y el servidor sin salida a la red. Nada
  podía pagar.
  - El paquete se importó una vez: 26 imágenes (V22 17, V18 5, V11 4), 72 filas del registro, el mismo
    presupuesto (US$2,4959; 26 de 30).
  - El panel docente muestra 7 imágenes utilizables y, con «Show rejected and excluded images too», las
    26, cada una con su motivo.
  - Un encuentro local del caso de 54 años mostró a V22 somnoliento (`fdde9713bb`) en el minuto 0, y la
    sala lo registró.
- **Defecto encontrado y corregido (C-2026-09-26-07):** la línea del presupuesto se veía como una
  fórmula («US2.50ofUS10.00…» en cursiva), porque Streamlit lee el texto entre dos signos de dólar como
  matemática. Ahora cada signo va escapado; la prueba nueva falla con el código anterior.
- **La barra lateral tapaba parte de la sala (C-2026-09-26-08, a pedido tuyo):** las capas de la sala
  estaban fijas a la ventana, y la barra abierta (300 px en un computador) cubría el minuto y el comienzo
  de la nota sobre lo que la foto no permite ver. Ahora la sala empieza donde termina la barra, sea cual
  sea su ancho. Revisado en un navegador real sobre la copia local, con la barra abierta y cerrada, a 1400,
  1280 y 1024 px, y en un teléfono, donde la barra se abre encima y la sala no cambia. Con la barra
  abierta, el monitor y la consola quedan proporcionalmente más angostos.
- **Consumo de esta revisión: 0 solicitudes, US$0.** El saldo sigue en US$7,5041 y 4 solicitudes, salvo
  lo que hayan usado los encuentros de la app de desarrollo después del reinicio: eso sólo se ve en su
  panel.

