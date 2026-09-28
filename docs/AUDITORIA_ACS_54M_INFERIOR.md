# Auditoría · `acs_54m_inferior`: VD comprometido en el caso, VD normal en su POCUS

Ciclo 5 del AI Advisor, autorización docente del 2026-09-28 (§23, §40, §41, §55).

**Estado: AUDITADO. NO CORREGIDO. REQUIERE DECISIÓN DOCENTE.**

- No se cambió ningún dato clínico del caso.
- C14 sigue **NOT REVIEWED** en este caso. Conserva sólo la regla de
  transición (`observation_opportunities`, DF-12).
- Las opciones A y B se simularon en copias descartables del código, fuera del
  repositorio, sólo para medir su impacto en las pruebas (sección 11).

## Resumen

- **El diseño del caso es un IAM inferior con compromiso del VD.** Lo dicen:
  - el comentario del caso;
  - la declaración coronaria (`rv_involvement: True`);
  - cuatro decisiones docentes que lo nombran «54m inferior con VD»;
  - el guion «bueno» de la tanda 20.
  El motor lo modela en seis lugares.
- **El POCUS dice VD normal.** Es un borrador nunca revisado
  (`POCUS_DRAFT_PENDING_FACULTY_REVIEW = True`). Su propia nota dejó la
  pregunta abierta: *«Dejé el VD normal. Si quieres que el caso incluya
  compromiso del VD, cambian el VD y la VCI.»*
- **En un mismo encuentro el residente ve las dos cosas.** Las derivadas
  derechas muestran SDST de 1.5 mm en V4R y el POCUS dice «RV free wall
  contracts normally». Si confía en el POCUS y da nitroglicerina a 20 mcg/min,
  la PA cae de 100/64 a 67/45 en 10 minutos.
- **Clasificación: B**, inconsistencia de datos del caso con consecuencia
  visible en el juego.
- **Recomendación: opción A** (corregir el POCUS al compromiso del VD), con la
  redacción exacta decidida por el docente.

## 1. Dónde aparece cada dato

**«Compromiso del VD»**

| Dónde | Qué dice |
|---|---|
| `clinical_cases.py:567-570` | `coronary={"omi": True, "territory": "inferior", "rv_involvement": True, "pci_capable": True, "symptom_onset_min": 75}`, con el comentario *«An inferior occlusion with right ventricular involvement: the artery has to be opened, and nitroglycerin can collapse a preload-dependent circulation.»* |
| `acs_reperfusion.py:126` (`nitrate_drop`) | *«Faculty decision 2026-09-19: model it in the bank case too.»* |
| `docs/REVISION_BANCO_2026-09-21.md`, §4 | *«En el 54m inferior con compromiso de VD e hipotensión…»* |
| `docs/DECISIONES_3_4_8_MAGNITUDES.md:61` (decisión 4) | columna «Infarto inferior con VD»: tolerancia de 1600 mL y parte precargo-dependiente 1.0 |
| `docs/DECISIONES_5_6_10_MAGNITUDES.md:120` (decisión 10) | «**54m inferior con VD** (PAS 98) · morfina 4 mg · 98 → 88» |
| `docs/DECISIONES_7_9_MAGNITUDES.md:31` (decisión 7) | «**54m inferior con VD**, ocluida: SDST 1.5 mm en V4R, 1 mm en V3R» |
| `tanda20.py:132-141` (guion 3, «bueno») | «IAM inferior con posible compromiso del VD… pido ECG con derivadas derechas. Espero documentar el VD…» |

**«VD normal»**

| Dónde | Qué dice |
|---|---|
| `clinical_cases.py:113-114` (`POCUS["acs"][0]`, que usa sólo este caso) | `rv="Smaller than the LV; RV free wall contracts normally; no septal flattening (no D-sign); no McConnell sign"` · `ivc="1.8 cm; about 50% inspiratory collapse"` |
| `clinical_cases.py:64` | `POCUS_DRAFT_PENDING_FACULTY_REVIEW = True` |
| `docs/POCUS_DRAFT_FINDINGS.md:133-154` («acs · variante 0») | la misma tabla, y la nota *«Dejé el VD normal. Si quieres que el caso incluya compromiso del VD, cambian el VD y la VCI.»* |
| `case_text/es/acs.json:77` | la traducción: «Menor que el VI; la pared libre del VD se contrae normalmente…» |

**Un detalle que pesa.** El texto del VD de este caso no es el normal por
defecto (`_RV_NORMAL`). Agrega «RV free wall contracts normally», así que
afirma explícitamente lo que el caso niega.

**La historia de git no dice el orden.** Todo entra en el primer commit del
repositorio (`8e33be5`, 2026-09-21). Pero la nota del borrador muestra que el
VD normal fue una elección provisional pendiente de decisión, no un diseño.

## 2. CASE DESIGN INTENT

- **Diagnóstico:** «Inferior ST-elevation myocardial infarction».
- **Rasgos clave:**
  - molestia persistente de esfuerzo con síntomas autonómicos;
  - SDST inferior con cambios recíprocos;
  - alteración regional de la motilidad del VI.
- **Objetivo docente:** reconocer el patrón isquémico tiempo-dependiente y
  gestionar la reperfusión vigilando la hemodinamia.
- **Intención respecto del VD:** compromiso del VD, sostenido por el
  comentario, la declaración coronaria y las decisiones docentes del
  2026-09-19 y del 2026-09-21 (sección 1).
  - La enseñanza que esas decisiones construyen: derivadas derechas, no
    nitratos, volumen prudente, morfina con cautela.
  - La conducta enseñada (decisión 4): *«bolo prudente → reevaluar →
    adaptar, nunca "infarto de VD, entonces volumen ilimitado"».*

## 3. CURRENT CASE DATA

- **Presentación:** hombre de 54 años con molestia epigástrica persistente y
  náuseas, sudoroso.
  - La historia la irradia al pecho y la mandíbula.
  - Hipertensión, dislipidemia, tabaquismo y antecedente familiar.
- **Signos:** PA 100/64 · FC 58 · SpO₂ 96 % · FR 22 · llene 3 s · extremidades
  frías · perfusión levemente comprometida.
- **Examen:**
  - pulso lento y regular, sin soplo nuevo;
  - pulmones limpios;
  - abdomen blando.
  - No se describe la presión venosa yugular.
- **ECG:** `st_elevation_inferior`.
- **Laboratorio:** troponina 95 ng/L · lactato 2.1.
- **Radiografía:** sin edema.
- **Nota de triaje:** «indigestion?», como impresión no confirmada (R1-07).
- **Estudios del caso:** incluye derivadas derechas y posteriores.

## 4. POCUS DATA

| Estructura | Llegada | Evolución en el motor |
|---|---|---|
| VI | «Reduced contraction of the inferior wall; the other walls contract normally» | Con minutos de isquemia, el modelo lo reemplaza por el grado de `lv_function`: «mildly reduced» y, pasados unos 48 minutos, «moderately reduced» |
| **VD** | **«Smaller than the LV; RV free wall contracts normally; no septal flattening (no D-sign); no McConnell sign»** | **Fijo**: no cambia nunca |
| **VCI** | **«1.8 cm; about 50% inspiratory collapse»** | **Fija**: en el SCA la VCI no responde al volumen; sólo en neumonía y hemorragia digestiva. Con VMNI o ventilación invasiva se agrega «no evaluable» |
| Pulmón | líneas A; deslizamiento presente; sin consolidación | fijo |
| Aorta, venas | normales | fijas |

- **Lo que un VD comprometido haría esperable:** VD dilatado con pared libre
  hipocinética y VCI pletórica con poco colapso, por la presión de la
  aurícula derecha elevada.
- **Lo que el POCUS muestra:** lo contrario, en las dos estructuras.

## 5. PHYSIOLOGIC STATE (lo que el motor modela con `rv_involvement: True`)

| Mecanismo | Con VD | Sin VD | Dónde |
|---|---|---|---|
| Deriva circulatoria de la oclusión | 0.0018/min | 0.0012/min | `acs_reperfusion.py:46-47, 254, 284` |
| Caída por nitroglicerina | la del infarto de VD de `nitrate_hazard`, rescatable con volumen | no aplica | `family_engine.py:1840`, `acs_reperfusion.nitrate_drop` |
| Respuesta al volumen (decisión 4) | tolerancia 1600 mL · parte precargo-dependiente 1.0 | 1000 mL · 0.6 | `preload_response.py:24-37` |
| Morfina (decisión 10) | factor 2.2 | según la PAS | `analgesia.py:33, 60` |
| Congestión pulmonar | ×0.5: el VD no moja el pulmón | ×1 | `acs_reperfusion.py:92, 108` |
| Derivadas derechas (decisión 7) | SDST 1.5 mm en V4R; se resuelve al abrir la arteria | «No ST elevation in V3R or V4R» | `acs_reperfusion.py:396-404` |
| Bloqueo AV a los 45 min | depende del territorio inferior, no del VD | igual | `acs_reperfusion.py:255` |

**Lo que el motor muestra hoy, en una sonda de sólo lectura** (el caso real y
el motor real, sin cambios):

| Encuentro | Resultado |
|---|---|
| Llegada + POCUS + derivadas derechas | 100/64 · FC 58. **V4R: SDST 1.5 mm.** **POCUS: VD con pared libre normal**; VCI 1.8 cm con 50 % de colapso |
| 30 min sin tratamiento | 96/62. El VI pasa a «mildly reduced»; **el VD y la VCI siguen igual** |
| Nitroglicerina 20 mcg/min, 10 min | **67/45** |
| Suero 500 mL, 20 min | 105/67 |
| Sólo aspirina, 20 min (referencia) | 97/63 |

La fisiología es coherente consigo misma: todo el motor trata al VD como
comprometido. Lo incoherente es lo que el POCUS muestra.

## 6. DECISION CHALLENGE

El caso pertenece a la familia SCA. Pueden servirlo tres desafíos:

- **R2-02**, sesgo de confirmación: buscar hallazgos que discriminen, incluso
  los que debilitan la hipótesis. La tanda 20 lo jugó aquí.
  - Es el desafío que más sufre la contradicción. El residente que busca
    evidencia discriminante recibe dos hallazgos que se contradicen (V4R
    positivo, VD normal), y no por diseño.
- **R1-07**, efecto de encuadre: la nota de triaje «indigestion?».
  - No depende del VD.
- **R2-04**, representatividad: la presentación epigástrica.
  - No depende del VD.

## 7. CRITICAL EVENTS

- **Eventos del caso:**
  - `acs_no_antiplatelet`;
  - `acs_provocation_test`.
- **Ninguno depende del VD**, y ninguna opción los cambia.
- **Un nitrato en el infarto de VD no es un evento crítico.** Su daño es
  fisiológico: la caída de PA es observable, en D4. D3 acepta como
  alternativa *«withholding a nitrate, which in this territory is a defensible
  choice»*.

## 8. EXPECTED MANAGEMENT

- **D3:** antiagregación y vía de reperfusión, *«with the preload caution an
  inferior territory carries»*.
- **D5:** reperfusión: quién abre la arteria y qué se vigila mientras.
- **Guion «bueno» de la tanda 20:**
  - aspirina y clopidogrel;
  - derivadas derechas;
  - sin nitratos;
  - hemodinamia;
  - traslado monitorizado.

El texto de la rúbrica sirve para las dos representaciones. El guion no: con
un VD normal, las derivadas derechas saldrían negativas y su razonamiento
(«espero documentar el VD») quedaría contradicho.

## 9. DEPENDENT TESTS

Medido en copias descartables del código (commit `828271e`), aplicando cada
opción.

- **El conjunto medido:** 2,540 pruebas de 90 archivos, todos los que
  mencionan SCA, POCUS, texto de caso, tanda 20, nitratos o coronaria.
- **La referencia:** 0 fallas en la suite completa del baseline español.

| Opción | Fallan | Qué fijan esas pruebas |
|---|---|---|
| **A** (POCUS con VD comprometido) | **1**: `test_case_text.py::test_every_drafted_passage_translates_what_its_case_says_today` | el texto español del caso tiene que traducir el inglés vigente: pide nueva traducción y aprobación docente |
| **B** (`rv_involvement: False`) | **2**: `test_acs_reperfusion.py::test_nitroglycerin_collapses_the_right_ventricular_infarct_and_volume_rescues_it` y `test_acs_respiratory_axis.py::test_the_right_ventricle_does_not_wet_the_lung` | dos decisiones docentes: la del 2026-09-19 (el nitrato en el infarto de VD del banco) y la de la congestión del VD |

- **Las demás pruebas pasan con A y con B.** Usan el caso como «el STEMI»:
  - reperfusión;
  - fibrilación a los 120 min;
  - curva de troponina;
  - bloqueo AV;
  - sobrecarga por transfusión.
- **Las pruebas de C14 lo tratan como NOT REVIEWED:**
  - `test_c14_opportunities.py`;
  - `test_c14_review.py`;
  - `test_observation_opportunities.py`.
  Declarar C14 para el caso, en cualquier opción, obliga a actualizarlas.

## 10. DEPENDENT OUTPUTS

- **Encuentros históricos: ninguna opción los toca.** El POCUS y la
  declaración coronaria se leen de la especificación congelada del encuentro
  (`family_engine._case`, `acs_reperfusion.coronary`). Un cambio sólo alcanza
  a los encuentros nuevos.
- **Texto en español** (`case_text/es/acs.json`): con A, el pasaje del VD y de
  la VCI se traduce de nuevo y vuelve a aprobación docente.
- **`docs/POCUS_DRAFT_FINDINGS.md`:** con A, se regenera.
- **Tanda 20 y corpus de ensayo** (guion 3): con B, la derivada derecha sale
  negativa y el guion se contradice. Con A, nada cambia: el guion no pide
  POCUS.
- **Piloto de validación:** ninguno. Sus seis casos (C01–C06) no incluyen SCA.
- **Imágenes:** ninguna. No hay imágenes de POCUS, y la foto de llegada no
  depende del VD.
- **C14:** queda NOT REVIEWED hasta la decisión.

## 11. CLASIFICACIÓN DE LA CONTRADICCIÓN

**B · inconsistencia de datos del caso.** El POCUS escrito contradice la
declaración coronaria escrita, y el residente la ve en el juego.

| Clase | Por qué sí o por qué no |
|---|---|
| A · sólo documentación | **No**: está en los datos que ve el residente |
| **B · datos del caso** | **Sí**: dos datos del mismo caso se contradicen |
| C · fisiología | **No**: la fisiología es coherente consigo misma; todo el motor trata al VD como comprometido |
| D · ambigüedad intencional | **No**: la nota del borrador muestra una elección provisional con la pregunta abierta |
| E · desconocida | **No**: las causas están identificadas |

## 12. POSIBLES CONCLUSIONES

### A · El compromiso del VD es lo correcto

Se corrigen el VD y la VCI del POCUS, y opcionalmente el examen (presión venosa
yugular).

- **Plausibilidad clínica: alta.** Es el infarto de VD clásico de la oclusión
  de la coronaria derecha:
  - hipotensión con pulmones limpios;
  - bradicardia;
  - SDST en V4R;
  - dependencia de la precarga;
  - sensibilidad a los nitratos.
- **Desafío:** R2-02 gana: la evidencia discriminante es coherente.
- **Manejo:** no cambia; el motor ya es de VD.
- **C14:** podría pasar a **YES**. El VD en el POCUS orienta a no dar nitratos
  y a dar volumen con prudencia, que es la lógica de la decisión A. Pero la
  respuesta C14 del caso la da el docente, después de corregir los datos.
- **Eventos críticos:** no cambian.
- **Pruebas:** 1, el texto en español; más las de C14 si se declara.
- **Compatibilidad:** sólo encuentros nuevos.
- **Límite que queda:** el VD y la VCI seguirían fijos. Al abrir la arteria,
  V4R se resuelve y el POCUS no, igual que la VCI estática de la
  pielonefritis 58f. Que evolucionen sería otra decisión, esta vez del motor.

### B · El VD normal es lo correcto

Se quita `rv_involvement`.

- **Plausibilidad clínica: alta.** Un IAM inferior sin VD es frecuente, y la
  PA 100/64 con FC 58 se explica por tono vagal y bradicardia.
- **Desafío:** pierde su hallazgo discriminante propio; V4R sale negativo.
- **Manejo:** cambia la trayectoria:
  - la nitroglicerina pasa a ser ordinaria;
  - tolerancia de 1000 mL;
  - morfina según la PAS;
  - deriva circulatoria más lenta.
- **Consecuencia sobre el banco:** las decisiones docentes 4, 7 y 10 se quedan
  sin caso del banco que las ejerza.
- **C14:** probablemente **NO**. El ECG ya establece el STEMI, como en
  `acs_66f_nonst`.
- **Eventos críticos:** no cambian.
- **Pruebas:** 2, que fijan decisiones docentes. El guion 3 de la tanda 20
  queda contradicho.
- **Compatibilidad:** sólo encuentros nuevos.

### C · Las dos cosas coexisten

Un infarto de VD con un VD que se ve normal en el POCUS.

- **Clínicamente posible** en un infarto de VD pequeño: la sensibilidad del
  POCUS es limitada y V4R es más sensible temprano.
- **Difícil de conciliar con la magnitud modelada.** Una caída a 67/45 con
  20 mcg/min de nitroglicerina es un infarto de VD hemodinámicamente
  significativo, que suele verse. Y el texto afirma que la pared libre se
  contrae normalmente.
- **Para ser intencional, el caso tendría que decirlo.** Por ejemplo, como
  punto docente: un POCUS normal no descarta el infarto de VD, igual que el
  Wellens de la decisión B. En ese caso C14 sería **NO**.
- **Pruebas:** no falla ninguna.
- **Riesgo:** el residente que confía en lo que el simulador le muestra es
  dañado por una fisiología que esos datos niegan. Afecta la validez de lo que
  se juzgue en D3 y D4.

### D · La intención no se puede determinar

**No lo sostiene la evidencia:** el comentario del caso, cuatro decisiones
docentes y la nota del borrador la determinan. Si se eligiera igual, el caso
seguiría NOT REVIEWED con la contradicción documentada.

## RECOMMENDATION

**Opción A.**

- **Por qué:** el compromiso del VD es el diseño. Lo sostienen el comentario
  del caso, cuatro decisiones docentes, el motor y el guion. El VD normal es
  un marcador provisional de un borrador no revisado, y el borrador mismo lo
  señaló.
- **Qué se corrige:** el VD y la VCI del POCUS de este caso, con la redacción
  que el docente apruebe.
  - La simulación de impacto usó, sólo para medir:
    - «Dilated, approximately equal to the LV; reduced free-wall contraction;
      no septal flattening (no D-sign); no McConnell sign»;
    - «2.3 cm; <50% inspiratory collapse».
  - No es una propuesta de texto clínico.
- **Después:**
  - se traduce de nuevo el pasaje en español, que vuelve a aprobación;
  - el docente responde C14 para el caso;
  - se registra la corrección en `corrections_registry`.

## IMPACT OF EACH OPTION

| | A | B | C | D |
|---|---|---|---|---|
| Datos que cambian | POCUS: VD y VCI (¿examen?) | `rv_involvement` | ninguno (o una nota docente) | ninguno |
| Fisiología | igual | cambia la trayectoria | igual | igual |
| Contradicción visible | se resuelve | se resuelve | queda, declarada | queda |
| Decisiones docentes 4, 7, 10 | siguen con su caso | se quedan sin caso | siguen | siguen |
| C14 probable | YES (decide el docente) | NO | NO | NOT REVIEWED |
| Pruebas que fallan | 1 | 2 | 0 | 0 |
| Texto en español | nueva traducción + aprobación | sin cambio | sin cambio | sin cambio |
| Tanda 20, guion 3 | sin cambio | contradicho | sin cambio | sin cambio |
| Encuentros históricos | intactos | intactos | intactos | intactos |

## DECISION NEEDED

1. **¿Cuál representación es la correcta?** A, B, C o D.
2. **Si A:**
   - el texto exacto del VD y de la VCI;
   - si el examen agrega la presión venosa yugular;
   - si el VD debe evolucionar al abrir la arteria (cambio del motor, aparte).
3. **Después:** C14 **YES** o **NO** para `acs_54m_inferior`.

Hasta entonces no se cambia nada.

## Otro hallazgo de esta auditoría (LOW, no es parte de la decisión)

- **El VI del POCUS cambia de redacción.** Al llegar dice «Reduced contraction
  of the inferior wall», sin grado. Con los primeros minutos de isquemia, el
  modelo escribe «The inferior wall shows mildly reduced contraction».
- **El valor subyacente es el mismo** (`ARRIVAL_LV = .82`, banda «mildly
  reduced»), pero puede leerse como una mejoría mientras el infarto avanza.
- **Queda en la lista de inconsistencias clínicas conocidas.** No se corrigió.
