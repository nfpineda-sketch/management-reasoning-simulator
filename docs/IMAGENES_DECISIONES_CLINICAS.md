# Imágenes del paciente: decisiones que te tocan

Agrupadas en un solo lugar, como pediste. Ninguna bloqueó el trabajo técnico, y ninguna se tomó por ti.

## Revisar lo generado

1. **Las 7 imágenes utilizables** (V22: ancla, somnoliento, obnubilado, recuperado; V18: ancla; V11: ancla,
   somnolienta). Están pendientes de revisión visual y clínica. Se revisan en «Patient image bank
   (faculty)». Una rechazada sale de la selección y queda en el registro.
2. **El banco de 30 personas** (`image_identities.py`): descriptores visuales, sin categorías raciales,
   repartidos por edad, sexo, tono, pelo y contextura. ¿Algún descriptor te parece poco respetuoso o
   ambiguo?

## Criterios visuales

3. **Equipo de sala.** El generador pone tomas de gases, reguladores y a veces bolsas o sets de infusión
   en la pared, sin conectar al paciente. ¿Es aceptable el equipo de pared no conectado, o toda bolsa y
   línea visible debe excluir la imagen?
4. **Vía venosa.** El motor modela el acceso venoso (por ejemplo «peripheral intravenous access already in
   place»), pero el contrato visual no lo incluye. Hoy la foto nunca muestra una vía. ¿Debe mostrarla
   cuando el caso o una orden ejecutada la tienen?
5. **Revisión humana sobre la automática.** El revisor automático rechazó 10 fotos de la mascarilla de
   reservorio que, a mi revisión, se ven correctas. ¿Puede tu revisión visual y clínica aprobada habilitar
   una imagen que el revisor automático rechazó? Hoy no. La decisión cambia una regla de seguridad.
6. **Sudor marcado sobre piel oscura.** No se logró en 4 candidatos. La sala muestra la vista neutral y
   el examen escrito. ¿Aceptas esa limitación, o prefieres probar otro modelo o configuración (con un
   nuevo presupuesto)? Nunca se sustituye por una persona de piel más clara.

## Frecuencia de imágenes nuevas

7. **Estados equivalentes.** Hoy cada combinación del contrato es una foto distinta. Hay dominios que el
   propio revisor declara no discernibles en una foto (sudor leve, palidez leve, esfuerzo leve). ¿Puede
   una foto sin sudor visible servir también para «sudor leve», rotulada como hoy? En los 20 guiones, lo
   que más cambia es el esfuerzo respiratorio (17 veces) y la expresión (14). Agrupar reduciría las
   imágenes, pero es un criterio clínico.
8. **Imágenes sin revisar para residentes.** Hoy, como antes, una foto que pasó la revisión automática se
   muestra aunque su revisión humana esté pendiente. Para producción, ¿exigir revisión visual o clínica
   antes de mostrarla?

## Antes de fusionar con `main`

9. **Presupuesto en producción.** Con este código toda imagen nueva exige un presupuesto vigente con tope.
   Al fusionar habrá que autorizar uno para la app pública (`MRS_IMAGE_BUDGET_ID`, `_USD`, `_REQUESTS`).
   Sin él, la sala muestra sólo lo guardado.
10. **Modo compartido.** Sin base de cuentas, la sala conserva el camino anterior, sin banco ni presupuesto
    persistente. ¿Se mantiene, o se desactivan las imágenes pagadas en ese modo?
