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

### Lote 1b (V22 de nuevo, con el método corregido)

- **Antes:** reserva máxima US$1,10 (ancla y estado, cada uno con su corrección) y 4 solicitudes. Gastado
  hasta aquí: US$0,2142; 3 solicitudes.
