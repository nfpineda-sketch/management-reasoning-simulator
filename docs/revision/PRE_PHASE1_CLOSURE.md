# Cierre pre-Fase 1 · 2026-10-15

Autorización del propietario del programa: crear `prephase1-closure-v1` desde el piloto promovido
`9abe6e585840f37c469030c442f927dc0163f794`, cerrar E2b y E1 y ordenar la gobernanza del lector y de dos
textos de presentación. `pilot-residents-v1` no se modifica sin una autorización posterior.

## Alcance

Dentro de este cierre:

1. **E2b · render durante Send.** Se desactiva el atajo que omitía el bedside/chart en el rerun que procesa una
   entrega durable. La escritura previa, la idempotencia y la ejecución no cambian.
2. **E1 · errores del store.** Una falla al obtener/liberar una conexión y una segunda falla al hacer rollback
   quedan convertidas al mismo `AccountError` genérico que ya protege los errores del cuerpo de una transacción.
   El log conserva sólo clase y ubicación, nunca el mensaje del driver.
3. **Reader freeze.** No se modifica el lector en este cierre. Se acepta como nuevo estado congelado la versión ya
   presente en `9abe6e58`: `family_parser.py` incluye cuatro correcciones del 2026-10-11 y los otros cuatro
   archivos del conjunto siguen byte a byte en V3. `test_prephase1_reader_freeze.py` fija los cinco blobs.
4. **Presentación en español.** Se acepta `Serum magnesium → Magnesio sérico` como etiqueta de presentación y se
   agrega la traducción del rótulo de `pacing_preparation` que alcanzaba el Management Trace en inglés:
   `preparación para marcapasos transcutáneo registrada; estimulación no iniciada`.

Fuera de alcance: fisiología, scoring, D1–D5, rúbrica, corpus de validación, V3, baselines, casos, esquema persistido,
pool sizing, duración del lock, número de escrituras por Send, Fase 1 Contracts v2, push/merge/deploy del piloto.

## Evidencia previa

### E2b reproducido en el piloto vigente

En `9abe6e58`, con la cuenta residente de prueba, después de cuatro `Reassess.` consecutivos, la respuesta más
reciente mostraba a los 23 min **BP 85/53, HR 133, SpO₂ 88%, RR 32**, mientras el monitor visible conservaba
**HR 132** y mostraba ghosting/superposición en el trazado y en dígitos. El primer Send había sido coherente.
Esto reproduce en el runtime vigente la clase de defecto hallada previamente sobre `020da651`.

### E1 verificado en el código

En el código base, la adquisición de `_borrow_connection()` ocurría fuera del `try` que sanitizaba excepciones del
driver. Además, dentro del handler, `connection.rollback()` podía fallar y sustituir el `AccountError` genérico.
El cierre protege ambos bordes y agrega regresiones que inyectan mensajes con host/contraseña falsos y comprueban
que no llegan al error expuesto.

### Lector posterior a V3

El conjunto congelado en V3 no estaba ya byte a byte intacto. `family_parser.py` recibió estas cuatro correcciones
posteriores:

- `edc31899` · Cover natural smoke-test orders conservatively.
- `a0d48ff7` · Fix monitoring wording and pacing preparation capture.
- `4080ec03` · Preserve pacing preparation category.
- `a93801c3` · Handle standalone shock-sign reassessment phrase.

No se revierten: ya forman parte del piloto probado. Desde este cierre quedan tratados como el estado aceptado del
lector, sin autorizar cambios adicionales ni abrir la validación externa.

## Freeze del lector aceptado

| Archivo | Git blob SHA |
|---|---|
| `family_parser.py` | `1d17bf8b3dce66da5f1c8291237e2e7a7afde1c0` |
| `shared_order_language.py` | `5ed6a8a14aa2f7cf077ffaf2a202ee9cf0bd8047` |
| `shared_order_quantities.py` | `65e3606a2fd80bc6fb1f988e48460e6b2f6f100c` |
| `active_order_context.py` | `3c0432f5711cfbd3a919649e1bbe52cce3afbaeb` |
| `weight_based_doses.py` | `cdf79e0e654e11f908a90eb91139c9812a2416e8` |

## Cierre v3 · Send antes del render (2026-10-16)

Los intentos de cierre centrados en `st.fragment`, en la identidad del fragmento y en el slot del bedside no
explicaron por completo el defecto hosted. La evidencia más reciente mostró varias copias de **todo el subárbol
del encuentro** —Management, modos y formulario— después de un Send. Por tanto, el problema no se trata como un
defecto del monitor: el flujo de rerun de la página estaba emitiendo una interfaz parcial antes de procesar la
entrega y luego terminaba con `st.rerun()`.

`prephase1-closure-v3` parte de `b21c345`, antes de esos intentos de render. La lógica que ya procesaba una
submission se extrae a `_process_submission_before_render(...)`. En cada run:

1. `capture` conserva el texto en el callback.
2. `write_ahead` lo persiste al comienzo del run siguiente, como antes.
3. Si existe una entrada `received`, se procesa **antes** de `_in_room` y antes de emitir bedside, chart,
   Management o el formulario.
4. El procesamiento conserva la misma lógica de parser, ledger, motor, Trace, eventos, `finish` y guardado.
5. `rerun_app()` inicia el run de resultado, y recién ese run dibuja una interfaz completa con el estado actual.

La ruta del formulario guiado delega en el mismo helper para no mantener dos implementaciones del procesamiento.
No cambian fisiología, reader, scoring, textos clínicos, persistencia ni esquema.

### Puerta hosted v3

Primero se prueba una sola orden `Reassess.`. Durante el procesamiento puede permanecer visualmente la página
anterior atenuada, pero al completar el run debe existir **una sola** interfaz del encuentro. No pueden aparecer
dos o más bloques Management/form. Si pasa, se repite cuatro veces y luego `Save & return`; el dashboard debe
quedar limpio.

## Puerta de salida

Antes de pedir promoción al piloto:

- pruebas focalizadas de E2b, E1, idioma y freeze en verde;
- suite completa en verde;
- 56/56 regresiones activas;
- smoke hosted del flujo Send: varios envíos consecutivos, respuesta y monitor concordantes, sin ghosting;
- smoke de retorno al Resident Dashboard, sin reaparición del bedside;
- confirmar que `pilot-residents-v1` sigue en `9abe6e58` hasta la autorización de promoción.

Sólo después de promover y verificar ese cierre se fija el nuevo `<SHA_FINAL>` para
`phase-1-contracts-v2`. WP0 sigue siendo el primer y único paquete autorizado al abrir Fase 1.
