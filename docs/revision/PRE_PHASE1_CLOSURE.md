# Cierre pre-Fase 1 · 2026-10-15

Autorización del propietario del programa: crear `prephase1-closure-v1` desde el piloto promovido
`9abe6e585840f37c469030c442f927dc0163f794`, cerrar E2b y E1 y ordenar la gobernanza del lector y de dos
textos de presentación. `pilot-residents-v1` no se modifica sin una autorización posterior.

## Alcance

Dentro de este cierre:

1. **E2b · render durante Send.** Tras los smokes hosted, la solución final es doble: el bedside deja de usar
   `st.fragment`, y el rerun intermedio que procesa una entrega durable vuelve a omitir el bedside/chart. Así el
   estado previo no se vuelve a dibujar durante el procesamiento y el rerun de resultado dibuja una sola sala con
   el estado actual. La escritura previa, la idempotencia y la ejecución no cambian.
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

## Cierre v2 · fragmento estable en hosted (2026-10-16)

El smoke hosted de `prephase1-closure-v1` en `b21c345` fue **NO-GO**: tras cuatro `Reassess.` el monitor volvió
a quedar superpuesto/stale y, después de `Menu → Save & return`, quedó una pantalla híbrida en vez del dashboard
limpio. E2b había desactivado el fast path, por lo que ese atajo no explicaba el defecto residual.

La ruta residual era la creación dinámica del wrapper:

```python
st.fragment(_room, run_every=every)(...)
```

dentro de `render_room` en cada rerun completo. En hosted, una instancia anterior podía seguir montada mientras
la nueva respuesta ya estaba visible.

El primer intento de `prephase1-closure-v2` usó una única función `@st.fragment` a nivel de módulo, pero el
smoke posterior a la promoción mostró que, al ingresar una orden, el navegador podía volver a mostrar dos bedside
durante la reconciliación. Por tanto, una identidad estable del fragmento no fue suficiente.

La corrección final elimina **por completo** `st.fragment` del bedside. `render_room` dibuja la sala como salida
normal del rerun completo y `clear_room_fragment` sólo limpia el estado transitorio de la imagen antes del
dashboard. Además, cuando existe una entrega durable pendiente, `fast_path` vuelve a omitir el render intermedio:
ese run procesa la orden sin volver a emitir la sala antigua y el rerun de resultado dibuja la sala actual una sola
vez. Se mantiene eliminado el polling automático de 2 s; una fotografía pendiente se actualiza en el siguiente
rerun normal/interacción. No cambian la fisiología, el monitor calculado, el Trace, el ledger, la persistencia ni la
ejecución de órdenes.

### Validación requerida para v2

1. Pruebas focalizadas: `test_resuscitation_room.py`, submission guard y registro de correcciones.
2. Regresiones activas 56/56.
3. Regenerar `docs/CATALOGO_HIPOGLICEMIA.md` después de la nueva entrada del registro y comprobar su test generado.
4. Hosted, misma secuencia que falló en v1: `Wait 20 minutes.` y cuatro `Reassess.`; un solo monitor, sin
   ghosting y con signos concordantes con la respuesta.
5. `Menu → Save & return to dashboard`; esperar 15 s y exigir dashboard limpio.

Hasta que 4 y 5 pasen, **NO-GO** para promover al piloto.

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
