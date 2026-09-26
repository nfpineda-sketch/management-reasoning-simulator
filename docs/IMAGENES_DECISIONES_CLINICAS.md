# Imágenes del paciente: decisiones que te tocan

Agrupadas en un solo lugar, como pediste. Ninguna bloqueó el trabajo técnico, y ninguna se tomó por ti.

## Respuestas del 2026-09-26 (tarde)

Respondiste «Aprobado» a todas, y aprobaste las 7 fotos del piloto («Apruébalas, se ven bien»). Así quedó
cada una (C-2026-09-26-09):

| # | Decisión | Qué hace ahora la aplicación |
|---|---|---|
| 1 | Las 7 fotos del piloto, aprobadas | Tus 14 revisiones (visual y clínica) viajan en `assets/patient_images/approvals.json`, a nombre de `npinedafaculty`, con la nota «registrada por el agente a su pedido». Se aplican al reiniciar la app; si esa cuenta no existe en una base, no se registran a nombre de nadie más. |
| 2 | Las 30 personas, sin cambios | Sin cambios. |
| 3 | Equipo de pared no conectado: aceptable | El revisor automático lo trata como equipo no conectado, salvo que una línea llegue al cuerpo del paciente. La generación sigue evitándolo. |
| 4 | Vía venosa visible cuando está indicada o ejecutada | Pendiente, en otra tanda (tu elección). |
| 5 | Tu revisión sobre la automática | Con las dos revisiones aprobadas, una foto rechazada por el revisor automático se usa. Nunca se levanta así la exclusión de una persona ni un retiro, y una revisión rechazada siempre la deja fuera. En el panel se lee «In use: approved … over the automated screen». |
| 6 | Sudor marcado en piel oscura: se acepta la limitación | No se pide: muestra la vista neutral y el examen escrito. En las tandas no se dibujó sudor marcado para nadie, para no atar el hallazgo al tono de piel. |
| 7 | Estados equivalentes | Sudor leve, palidez leve y esfuerzo levemente aumentado se dibujan como su basal y comparten foto; al lado se dice «not discernible in this still view». Las fotos ya guardadas se reubican solas al arrancar. |
| 8 | Revisión humana antes de mostrar, en producción | `MRS_IMAGE_REQUIRE_REVIEW=on` la exige (visual y clínica aprobadas). En desarrollo queda apagado. Al fusionar hay que encenderlo. |
| 9 | Presupuesto de producción | Al fusionar: `MRS_IMAGE_BUDGET_ID`, `_USD`, `_REQUESTS`. |
| 10 | Modo sin cuentas | Sin base de cuentas no se paga ninguna foto (tu elección): ni al lanzar ni en la sala. |

## Lo que queda para tu revisión

- **Las 37 fotos nuevas** de la segunda autorización, en «Patient image bank (faculty)». Débiles a mi
  juicio: V03 · asma y V17 · cólico renal (cara tranquila), V02 y V26 · anafilaxia (sin enrojecimiento
  visible).
- **pulmonary_edema_75f** no tiene foto de llegada: V11 (rechazada por el revisor, cuello «relajado») y V12
  (sin veredicto) muestran el malestar marcado. Si apruebas una en ambas revisiones, la sala la usa
  (decisión 5).
- **Las 10 del piloto con mascarilla de reservorio** y las rechazadas de V27, V21, V02 y V14: puedes
  aprobarlas si te parecen correctas (decisión 5).
- **Siete casos llegan con sudor marcado** y no tienen foto (pulmonary_edema_58m, acs_54m_inferior,
  acs_52m_de_winter, acs_70f_left_main, hypoglycemia_28m, obstructive_pyelonephritis_58f,
  trauma_limb_hemorrhage_27m). Probar otro modelo sería un presupuesto nuevo.

## Las preguntas originales

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
