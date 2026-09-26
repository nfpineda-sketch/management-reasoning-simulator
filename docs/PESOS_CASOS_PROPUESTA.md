# Peso de los casos: propuesta para tu revisión (2026-09-26)

**Estado: propuesta.** Hoy no se ha aplicado nada: los 31 casos siguen sin peso y el motor los calcula a
70 kg. Tampoco cambian la fisiología ni los criterios, no se registró ninguna aprobación y no se gastó
dinero. Este documento responde la decisión 11 de `IMAGENES_DECISIONES_CLINICAS.md`: la tabla caso por
caso, lo que cambia en el motor si la apruebas, y la revisión de las fotos con esos pesos.

## En corto

- **Distribución propuesta:** 8 casos con peso normal, 11 con sobrepeso, 10 con obesidad y 2 con obesidad
  severa. Son 39% obesos, entre Chile (34%) y EE.UU. (40%). Los pesos se eligieron **sin mirar las fotos**:
  la foto sigue al caso, nunca al revés.
- **Fotos:** hoy 23 casos tienen foto de llegada. Con estos pesos, 11 la conservan y 12 la pierden, porque
  su persona es delgada y el caso ya no. Cinco de esos 12 tienen reemplazo ya fotografiado (V38, V19 o
  V33) y sólo les falta la foto de llegada. Los otros siete necesitan personas nuevas.
- **Antes de aplicar hay cuatro decisiones clínicas tuyas** (sección «Qué cambia en el motor»). La más
  importante es la del volumen corriente: con peso real, un asmático de 105 kg recibiría 840 ml a 8 ml/kg.
  El peso predicho da 570 ml.

## Cómo se eligieron

- **Talla:** 1,73 m en hombres y 1,60 m en mujeres (entre Chile y EE.UU.), menos 3 cm desde los 70 años.
  Cada caso se corre ±3 cm con un valor fijo que sale de su nombre, para que no midan todos lo mismo.
- **Peso:** IMC objetivo × talla². El IMC objetivo es 22,5 para normal, 27,5 para sobrepeso, 34 para
  obesidad y 42 para obesidad severa.
- **Peso predicho (PBW, Devine):** 50 kg en hombres y 45,5 kg en mujeres, más 0,91 × (talla en cm −
  152,4). Es el que se usa para el volumen corriente y para los bloqueantes no despolarizantes.
- **Reparto:**
  - **Independiente del diagnóstico.** Cada familia tiene al menos un caso normal o con sobrepeso y uno
    más pesado, para que la contextura no sea una pista.
  - **Por edad, como en la población.** La obesidad se concentra entre los 34 y los 66 años. Los muy
    jóvenes y los mayores de 75 son normales o tienen sobrepeso.
  - **Dos casos quedan normales por su propia historia:** `hypoglycemia_54m_thiamine` (alcohol, baja
    ingesta) y `pulmonary_embolism_61m` (quimioterapia).

| | Normal | Sobrepeso | Obesidad (severa) |
|---|---|---|---|
| EE.UU., NHANES 2021–23 | ~28% | 32% | 40% (9%) |
| Chile, ENS 2016–17 | ~26% | 40% | 34% (3%) |
| **Esta propuesta (31 casos)** | 26% | 35% | 39% (6%) |

## La tabla

«Foto de llegada hoy» lista las personas que tienen hoy una foto utilizable del estado de llegada del
caso. «Con este peso» dice si esas fotos siguen siendo compatibles con la regla actual: el peso típico de
la contextura de la persona debe estar a 15 kg o menos del peso del caso.

| Caso | Edad · sexo | Antecedentes | Contextura | Talla | Peso | IMC | Peso predicho | Foto de llegada hoy | Con este peso |
|---|---|---|---|---|---|---|---|---|---|
| `pneumonia_46f` | 46 · F | artritis reumatoide | obesidad severa | 1,58 m | 105 kg | 42,1 | 51 kg | V05, V09 | **se pierde** |
| `pneumonia_83m` | 83 · M | HTA, hipoacusia | normal | 1,69 m | 64 kg | 22,4 | 65 kg | V29 | se conserva |
| `pulmonary_edema_58m` | 58 · M | HTA | obesidad | 1,74 m | 103 kg | 34,0 | 70 kg | — (sudor marcado) | — |
| `pulmonary_edema_75f` | 75 · F | IC con FE reducida, ERC | sobrepeso | 1,57 m | 68 kg | 27,6 | 50 kg | — (V11 y V12 en revisión) | ambas compatibles |
| `acs_54m_inferior` | 54 · M | HTA, dislipidemia | sobrepeso | 1,72 m | 81 kg | 27,4 | 68 kg | — (sudor marcado) | — |
| `acs_66f_nonst` | 66 · F | DM2, HTA | obesidad | 1,63 m | 90 kg | 33,9 | 55 kg | V11, V12 | **se pierde** |
| `acs_61m_posterior` | 61 · M | HTA, ex tabaquismo | sobrepeso | 1,74 m | 83 kg | 27,4 | 70 kg | V22, V23, V24, V26, V27 | **se pierde** |
| `acs_52m_de_winter` | 52 · M | dislipidemia | obesidad | 1,71 m | 99 kg | 33,9 | 67 kg | — (sudor marcado) | — |
| `acs_48m_wellens` | 48 · M | tabaquismo | sobrepeso | 1,73 m | 82 kg | 27,4 | 69 kg | V21, V22, V23, V24 | **se pierde** |
| `acs_70f_left_main` | 70 · F | DM2, HTA, ERC | sobrepeso | 1,58 m | 69 kg | 27,6 | 51 kg | — (sudor marcado) | — |
| `pulmonary_embolism_33f` | 33 · F | cirugía reciente de tobillo | sobrepeso | 1,59 m | 70 kg | 27,7 | 52 kg | V05 | se conserva |
| `pulmonary_embolism_61m` | 61 · M | cáncer de colon en quimioterapia | normal | 1,73 m | 67 kg | 22,4 | 69 kg | V24 | se conserva |
| `asthma_24f` | 24 · F | asma, rinitis alérgica | normal | 1,63 m | 60 kg | 22,6 | 55 kg | V03 | se conserva |
| `asthma_49m` | 49 · M | asma, UCI previa por asma | obesidad | 1,76 m | 105 kg | 33,9 | 71 kg | V23 | **se pierde** |
| `gi_bleed_57m` | 57 · M | artrosis de rodilla | obesidad severa | 1,73 m | 126 kg | 42,1 | 69 kg | V22, V23, V24 | **se pierde** |
| `gi_bleed_72f` | 72 · F | úlcera péptica previa, artrosis | sobrepeso | 1,54 m | 65 kg | 27,4 | 47 kg | V11, V12 | se conserva |
| `hypoglycemia_28m` | 28 · M | DM1 | normal | 1,75 m | 69 kg | 22,5 | 71 kg | — (sudor marcado) | — |
| `hypoglycemia_76f` | 76 · F | DM2, ERC | sobrepeso | 1,55 m | 66 kg | 27,5 | 48 kg | V11 | se conserva |
| `hypoglycemia_54m_thiamine` | 54 · M | consumo problemático de alcohol, baja ingesta | normal | 1,71 m | 66 kg | 22,6 | 67 kg | V22 | se conserva |
| `opioid_35m` | 35 · M | lumbago reciente | obesidad | 1,70 m | 98 kg | 33,9 | 66 kg | V17, V18 | **se pierde** |
| `opioid_67f` | 67 · F | dolor musculoesquelético crónico, ERC | sobrepeso | 1,62 m | 72 kg | 27,4 | 54 kg | V12 | se conserva |
| `anaphylaxis_29f` | 29 · F | rinitis estacional | normal | 1,63 m | 60 kg | 22,6 | 55 kg | V02 | se conserva |
| `anaphylaxis_63m_betablocked` | 63 · M | HTA, FA | obesidad | 1,73 m | 102 kg | 34,1 | 69 kg | V26 | **se pierde** |
| `renal_colic_34m` | 34 · M | — | obesidad | 1,75 m | 104 kg | 34,0 | 71 kg | V17 | **se pierde** |
| `obstructive_pyelonephritis_58f` | 58 · F | DM2 | obesidad | 1,60 m | 87 kg | 34,0 | 52 kg | — (sudor marcado) | — |
| `bradycardia_ccb_68m` | 68 · M | HTA, FA | sobrepeso | 1,76 m | 85 kg | 27,4 | 71 kg | V26, V27 | **se pierde** |
| `bradycardia_avb3_78f` | 78 · F | HTA, ERC | normal | 1,59 m | 57 kg | 22,5 | 52 kg | V14 | se conserva |
| `bradycardia_bb_54f` | 54 · F | HTA, migraña | obesidad | 1,63 m | 90 kg | 33,9 | 55 kg | V09 | **se pierde** |
| `bradycardia_hyperk_63m` | 63 · M | ERC terminal en hemodiálisis, DM2 | sobrepeso | 1,70 m | 79 kg | 27,3 | 66 kg | V22, V23, V24, V26, V27 | se conserva |
| `trauma_limb_hemorrhage_27m` | 27 · M | — | normal | 1,72 m | 67 kg | 22,6 | 68 kg | — (sudor marcado) | — |
| `trauma_hemothorax_41m` | 41 · M | — | obesidad | 1,72 m | 101 kg | 34,1 | 68 kg | V21 | **se pierde** |

Si quieres cambiar un caso, basta con decirme la fila. Cambiar un caso no obliga a cambiar los demás. En
`bradycardia_hyperk_63m`, el peso es el **peso seco**. ¿Lo dejamos dicho así en la ficha?

## Qué cambia en el motor si apruebas los pesos

Hoy el motor usa el peso del caso, o 70 kg si no tiene, en varios lugares. **La obesidad no cambia la
fisiología del motor:** no agrega hipoventilación, vía aérea difícil ni otra farmacocinética. Sólo cambian
las cantidades por kilo. Estas son las decisiones que te tocan antes de aplicar:

| # | Dónde | Hoy | Con 105–126 kg | Propongo |
|---|---|---|---|---|
| A | **Ficha del paciente** | No muestra peso ni talla. | El lector dejaría de preguntar el peso y usaría uno que el residente nunca vio. | Mostrar peso y talla en la ficha, como en urgencia. Es condición para las demás. |
| B | **Volumen corriente y ventilación requerida** (`asthma_ventilation`) | ml/kg × peso real; 8 ml/kg por defecto. | `asthma_49m`: 840 ml en vez de 570 ml. El atrapamiento aéreo del modelo lo castigaría como error del residente. | ml/kg × **peso predicho**, que es lo que significa «ml/kg» en ventilación. La ventilación minuto requerida (0,10 L/kg/min) también, con peso predicho. |
| C | **Bloqueantes neuromusculares** (`airway_pharmacology`) | mg/kg sobre peso real. | 100 mg de rocuronio a 126 kg cuentan como 0,8 mg/kg (parálisis más corta), cuando por peso ideal son 1,45 mg/kg. | Rocuronio, vecuronio y cisatracurio sobre **peso ideal** (el mismo número que el predicho). Succinilcolina sobre **peso real**. |
| D | **Diuresis basal** (`urine_output`) | 1,0 ml/kg/h × peso real. | Un paciente de 126 kg orinaría 1,8 veces lo de uno de 70 kg. | Diuresis basal sobre **peso predicho**. Los criterios no usan umbrales en ml/kg/h, así que no se tocan. |
| E | **Infusiones por kilo** (noradrenalina, dobutamina, sedación en µg/kg/min o mg/kg/h) | Peso real. | Coherente con la práctica habitual. | Sin cambio. |
| F | **Dosis por kilo que escribe el residente** (`weight_based_doses`) | Pregunta el peso, porque el caso no lo tiene. | Usaría el peso de la ficha sin preguntar. | Sin cambio en el lector. Qué peso corresponde a cada fármaco (enoxaparina, aminoglicósidos) lo juzga la evaluación, no el lector. |

B, C y D necesitan la talla del caso. Por eso la tabla trae talla además de peso.

## Las fotos

### Contextura aparente de las 20 personas fotografiadas

Mi lectura de las referencias. Es visual, no una medición.

| Persona | Rotulada | Se ve |
|---|---|---|
| V02, V03, V05, V09 (mujeres jóvenes y de mediana edad) | normal | delgadas; V03 y V09, muy delgadas |
| V11, V12, V14 (mujeres mayores) | normal | normal |
| V17, V18, V21 (hombres) | normal | atléticos o en forma |
| V22, V23, V24, V26, V27, V29 (hombres de 55 a 85 años) | normal | normal; V24, algo más robusto |
| V08 | sobrepeso | sobrepeso, bien logrado |
| V19 | obesidad | **entre sobrepeso y obesidad leve**: cara llena, pero el abdomen casi no levanta la frazada |
| V33 | obesidad | obesidad, bien logrado |
| V35 (rechazada por el revisor automático) | obesidad | obesidad, bien lograda y con dignidad |
| V38 | obesidad severa | obesidad (probablemente severa), bien logrado |

Tu impresión de «todos atléticos» se confirma en las 16 personas del primer banco. Las cinco de la tanda de
contextura sí se ven como se pidió; V19 queda algo corto.

### La tolerancia de 15 kg: una decisión

Tres casos de hombres con sobrepeso (`acs_61m_posterior` 83 kg, `acs_48m_wellens` 82 kg y
`bradycardia_ccb_68m` 85 kg) pierden sus fotos de hombres de contextura normal. Pesan entre 15 y 18 kg más
que un hombre normal de talla típica (67 kg).

- **Mantener 15 kg (lo que recomiendo).** Un hombre de IMC 27 tiene barriga visible, y el pedido fue
  justamente que no se vieran todos en forma. Necesita fotos de V40 y de V37 (hombres con sobrepeso,
  aún sin foto).
- **Subir a 20 kg.** Esos tres casos conservan sus fotos actuales sin gasto. Los obesos siguen perdiéndolas
  igual: la tolerancia no los rescata.

No toqué la regla ni los pesos para salvar fotos. Ajustar los pesos al banco sería cambiar un dato clínico
por una imagen.

### Fotos nuevas que harían falta si apruebas

Cuento sólo los casos sin sudor marcado. Los siete con sudor marcado siguen sin foto por la decisión 6.

| Caso | Persona | Qué se pide |
|---|---|---|
| `pulmonary_edema_75f` | V11 o V12 | **Nada:** basta tu aprobación de `532d7202` o de `96970e9c` (ver abajo) |
| `gi_bleed_57m` | V38 | llegada |
| `bradycardia_bb_54f` | V33 (o V35 si la apruebas) | llegada |
| `trauma_hemothorax_41m` | V19 | llegada |
| `opioid_35m` | V36 (obesidad, 20–30 años) o V19 | referencia + llegada (V36); sólo llegada (V19) |
| `renal_colic_34m` | V19 o V36 | llegada. **Riesgo:** el malestar marcado ya salió con la cara tranquila en V17 |
| `pneumonia_46f` | V32 (obesidad severa, 40 años) | referencia + llegada |
| `acs_66f_nonst` | V34 (obesidad, 60–70 años) | referencia + llegada |
| `asthma_49m` | V39 (obesidad, 50–60 años) | referencia + llegada |
| `anaphylaxis_63m_betablocked` | V39 o V25 | llegada. **Riesgo:** el enrojecimiento no salió ni en V02 ni en V26 |
| `acs_61m_posterior`, `bradycardia_ccb_68m` | V40 (sobrepeso, 60–70 años) | referencia + dos llegadas |
| `acs_48m_wellens` | V37 o V20 | referencia + llegada |

Son unas 6 referencias y 12 llegadas: 18 imágenes. Con la tasa de aciertos de la segunda tanda, unas 1,9
solicitudes por imagen utilizable, serían entre 30 y 35 solicitudes, alrededor de **US$2,5–3,0** reales.

- **El dinero alcanza:** el saldo de la segunda autorización es US$4,278.
- **El tope de seguridad no alcanza:** quedan 30 de las 100 solicitudes. Para hacerlo todo habría que
  subir ese tope (no el dinero) o dejar fuera los dos casos con riesgo (cólico renal y anafilaxia), que
  son los que más probablemente terminen en imágenes rechazadas.

### Recomendación por foto (pendientes de tu revisión)

Es sólo una recomendación: **no registré ninguna aprobación.** Una aprobación vale para la foto en todos
los casos compatibles, no sólo en el de hoy. Por eso tiene sentido aunque la foto deje de usarse en un
caso por su peso.

**Referencias (17): aprobar todas.** V02, V03, V05, V08, V09, V12, V14, V17, V19, V21, V23, V24, V26, V27,
V29, V33 y V38 son personas coherentes, con la sala limpia y sin tratamiento activo. La nota sobre V19
está arriba.

**Estados (24):**

| Foto | Estado pedido | Recomiendo | Por qué |
|---|---|---|---|
| V02 `b5db3e20` | malestar, respiración aumentada, enrojecida | **no aprobar** | Cara tranquila, sin enrojecimiento. Es la llegada de la anafilaxia. |
| V03 `f7b26ce2` | malestar marcado, esfuerzo marcado | **no aprobar** | Mirada inquieta, pero boca cerrada y hombros relajados. No es una crisis asmática. |
| V05 `5b68b30e` | malestar, respiración aumentada | aprobar con reserva | Casi neutral. El texto lleva la taquipnea. |
| V09 `6b6eca45` | malestar | aprobar | |
| V09 `88ab1e0e` | malestar, respiración aumentada | aprobar con reserva | Malestar sí, esfuerzo no visible. |
| V11 `ec9315a6` | malestar | aprobar | |
| V11 `a734490c` | obnubilada | aprobar | |
| V12 `fa2a94af` | obnubilada, respiración disminuida | aprobar | |
| V12 `f69b7508` | malestar | aprobar | |
| V14 `ab017b3c` | somnolienta, malestar | aprobar | |
| V17 `6138b1dc` | malestar marcado | **no aprobar** | Cara tranquila en un cólico renal. |
| V17 `c0d772c1` | obnubilado, respiración disminuida | aprobar | |
| V18 `a0ad2024` | obnubilado, respiración disminuida | aprobar | |
| V21 `9cf84f16` | malestar, respiración aumentada | **no aprobar** | Igual a la referencia neutral. |
| V21 `ca87e8ee` | malestar | aprobar con reserva | Malestar muy leve. |
| V22 `791a32bd` | malestar | aprobar | |
| V23 `ad05d22b` | somnoliento, malestar marcado, esfuerzo severo | aprobar | Boca abierta, cabeza caída. De las mejores. |
| V23 `2f626c73` | malestar | aprobar | |
| V24 `92c0a925` | malestar, esfuerzo marcado | aprobar | Boca entreabierta, esfuerzo visible. |
| V24 `ed245064` | malestar | aprobar | |
| V26 `f9076976` | somnoliento, respiración aumentada, enrojecido | aprobar con reserva | Somnolencia bien lograda; enrojecimiento no visible. Al lado se lee «not discernible». |
| V26 `df73eae5` | malestar | aprobar | |
| V27 `868e3acf` | malestar | aprobar | |
| V29 `e0fe0c84` | somnoliento, respiración aumentada | aprobar | |

**Fuera de la selección que recomiendo aprobar** (decisión 5: con tus dos revisiones aprobadas, la sala
las usa). Se ven en el panel con «Show rejected and excluded images too»:

- **Llegada de `pulmonary_edema_75f`, que hoy no tiene foto.** Basta una de estas dos:
  - **V12 `96970e9c`** · malestar marcado, esfuerzo marcado, sin veredicto del revisor. Boca abierta,
    disnea evidente, pared limpia. Tiene un lazo blanco en la muñeca que podría leerse como pulsera.
  - **V11 `532d7202`** · lo mismo, rechazada por el revisor. Angustia visible. El revisor vio
    «tratamiento activo»; en la pared sólo hay equipo sin conectar (decisión 3).
- **V35 `ebe16847`** · referencia. Obesidad bien lograda. El revisor vio el mismo «tratamiento activo»:
  tubos enrollados en la pared, sin conexión.

Las demás rechazadas de V02 y V11 no aportan nada que no tenga ya una foto utilizable. Las diez
con mascarilla de reservorio y el sudor marcado en V18 quedan fuera por diseño (decisión 6 y la mascarilla
que el generador no dibuja bien).

## Si apruebas, en este orden

1. Pesos y tallas en los casos, con las decisiones A–D, y sus pruebas.
2. Las fotos: tus aprobaciones en el panel, luego la tanda de fotos nuevas, en lotes controlados como la
   anterior.
3. Después, la vía venosa visible (decisión 4).
