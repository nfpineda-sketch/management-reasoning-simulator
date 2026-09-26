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

## Contextura corporal: lo que falta y una decisión nueva (2026-09-26, noche)

**Lo que faltaba.** Las 30 personas del banco tenían sólo «slim», «average» o «sturdy», y el generador
las dibujó a todas delgadas o en forma. Ninguna con sobrepeso u obesidad, cuando en ambas ciudades son la
mayoría de los adultos:

| | Normal | Sobrepeso | Obesidad |
|---|---|---|---|
| EE.UU., NHANES 2021–23 (adultos ≥20) | ~28% | 32% | 40% (9% severa); 46% entre 40 y 59 años |
| Cleveland (ciudad), CDC 2022 | | | 45% |
| Chile, ENS 2016–17 (≥15 años) | ~26% | 40% | 34% (3% mórbida) |

En tono de piel, el banco tenía los seis tonos por igual. Cleveland es 47% afroamericana, 32% blanca no
hispana y 13% hispana; Santiago es mayoritariamente mestiza, con 9% que se declara mapuche (Censo 2017) y
cerca de 13% de migrantes (sobre todo venezolanos, peruanos, colombianos y haitianos). El tono de piel es
una aproximación gruesa de todo eso; el banco no usa categorías raciales.

**Lo que hice (identidades 1.1, C-2026-09-26-10):**

- La contextura es una dimensión propia: normal, sobrepeso, obesidad y obesidad severa, en palabras
  clínicas simples y «realista, con dignidad, nunca exagerada»; la normal dice «no atlética».
- Diez personas nuevas (V31–V40), casi todas más pesadas y la mayoría en los tonos oliva y cálidos de
  Santiago y del Cleveland hispano; y las catorce que aún no tenían foto recibieron la contextura que la
  distribución necesita. Las dieciséis ya fotografiadas no cambian: su foto es cómo se ven.
- Resultado: 40 personas, 55% con sobrepeso u obesidad (antes, ninguna). Tonos: 5, 6, 10, 6, 7 y 6 del
  más claro al más oscuro. La contextura no depende del tono ni del diagnóstico; cada banda de edad y sexo
  sigue teniendo un tono claro, uno medio y uno oscuro.
- Piloto de cinco referencias (US$0,36): el generador dibuja bien sobrepeso, obesidad y obesidad severa.

**La contextura sigue al peso del caso**, como la edad y el sexo. Y aquí está la decisión:

## 11. Peso de los casos (nueva, tuya)

Ningún caso del banco declara peso. El lector le pide el peso al residente para las dosis por kilo, pero
el motor calcula a **70 kg** las infusiones por kilo, la diuresis por kilo y el volumen corriente. Una foto
de un paciente obeso en un caso que el motor trata como de 70 kg llevaría al residente a estimar, dosificar
y juzgar la diuresis con un peso que el motor no usa. Por eso hoy **los casos sin peso sólo muestran
contextura normal o sobrepeso**, y la obesidad queda para los casos generados por IA, que sí traen peso.

Para que los obesos aparezcan en los casos del banco, cada caso necesita un **peso (y talla) verificados**:
es un dato clínico que cambia dosis y fisiología, así que es tu decisión. Te propongo:

- Repartir pesos entre los 31 casos según la distribución real de su edad y sexo (del orden de 8 normales,
  11 con sobrepeso, 10 obesos y 2 con obesidad severa), **independientes del diagnóstico** para que la
  foto no se vuelva pista.
- Mostrar el peso en la ficha del paciente, como en un servicio de urgencia real.
- Te preparo la tabla caso por caso para que la revises antes de aplicarla.

La otra opción es dejar los casos sin peso: el banco se ve más real que antes (sobrepeso incluido), pero la
obesidad sólo aparece en casos generados.


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
