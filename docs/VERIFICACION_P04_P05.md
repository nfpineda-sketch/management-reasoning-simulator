# Verificación de la evidencia de P-04 y P-05 (TEP)

2026-09-30, a pedido docente (respuesta al paquete del ciclo 10, puntos 5 y 7).

> **Decididas e implementadas el 2026-09-30 (segunda respuesta):** P-04 **B con condiciones** (C-2026-09-30-06) y
> P-05 **D como simplificación explícita** (C-2026-09-30-07). La regla final y las trayectorias están en
> `docs/PULMONARY_EMBOLISM_MAGNITUDES.md`, sección «Regla final y cambios del 2026-09-30». Este documento queda
> como la evidencia que se presentó.

## Cómo se verificó y con qué límite

- **Fuentes buscadas:** el ensayo, el metaanálisis, el registro y la guía que responden cada pregunta.
- **Acceso:** esta sesión no puede abrir `pubmed.ncbi.nlm.nih.gov`, `www.nejm.org` ni `www.ebi.ac.uk` (política de
  red del entorno). Los datos salen de **extractos del buscador sobre las páginas de las publicaciones primarias**
  (PubMed, las revistas) y, donde se indica, de dos resúmenes secundarios (ACC, The Bottom Line). No leí textos
  completos.
- **Regla aplicada:** sólo se cita una cifra que apareció en esos extractos. Las cifras que no aparecieron no se
  citan (por ejemplo, los porcentajes de hemorragia intracraneal del metaanálisis de 2014).
- **Lo que no hice:** citar de memoria.

## P-04 · Qué hace una trombólisis no indicada

### A. Beneficio de reperfusión o hemodinámico en TEP de riesgo intermedio (submasivo)

**PEITHO** (Meyer y cols., *N Engl J Med*, 10 de abril de 2014; DOI 10.1056/NEJMoa1302097):

| | |
|---|---|
| **Población** | 1006 adultos normotensos con TEP agudo confirmado, disfunción del VD en ecocardiograma o angio-TC y troponina I o T positiva (riesgo intermedio) |
| **Intervención** | Un bolo IV único de tenecteplasa ajustado al peso (30–50 mg) más heparina, frente a placebo más heparina |
| **Desenlace primario** | Muerte o descompensación hemodinámica a 7 días: **13/506 (2,6 %) frente a 28/499 (5,6 %)** |
| **Mortalidad a 30 días** | 12 (2,4 %) frente a 16 (3,2 %) |
| **Seguimiento largo** (Konstantinides y cols., *JACC* 2017) | 709 pacientes de 28 centros, mediana de 37,8 meses: mortalidad 20,3 % frente a 18,0 % (p = 0,43) |
| **Limitaciones** | El beneficio fue prevenir la descompensación, no la muerte; sin beneficio de supervivencia a largo plazo; dosis plena en bolo; sólo normotensos |

**Goldhaber y cols.** (*Lancet*, 27 de febrero de 1993): 101 pacientes con TEP, alteplasa frente a heparina.

- La alteplasa mejoró significativamente más y antes la función del VD y la perfusión pulmonar.
- A los 7 y 30 días la resolución por gammagrafía de perfusión fue igual.
- Sin diferencia significativa en mortalidad ni recurrencia.
- Hubo 5 recurrencias clínicas sospechadas (2 fatales) a 14 días con heparina sola, y ninguna con alteplasa.
- **Limitaciones:** ensayo pequeño y antiguo.

**Guía ESC 2019**, texto citado:

> «thrombolytic treatment of acute PE restores pulmonary reperfusion more rapidly than anticoagulation with UFH
> alone. The early resolution of pulmonary obstruction leads to a prompt reduction in pulmonary artery pressure
> and resistance, with concomitant improvements in RV function».

La misma guía reserva la trombólisis sistémica para el TEP de alto riesgo, inestable; esto último se verificó en
el resumen del ACC.

**Wang y cols.** (*Chest* 2010), alteplasa 50 mg/2 h frente a 100 mg/2 h: la mejoría de la dilatación del VD, de
los defectos de perfusión y de la obstrucción arterial pulmonar fue similar con ambas dosis.

### B. Aumento de sangrado mayor y de hemorragia intracraneal

**PEITHO:**

- Sangrado mayor extracraneal: **32 (6,3 %) frente a 6 (1,2 %)**.
- ACV: **12 (2,4 %) frente a 1 (0,2 %)**; hemorrágico en 10 frente a 1.
- Según un resumen secundario (The Bottom Line), 8 de los 13 ACV ocurrieron en mayores de 75 años.

**Chatterjee y cols.** (*JAMA* 2014;311(23):2414-21), metaanálisis de 16 ensayos (2115 pacientes):

- En los 8 ensayos de riesgo intermedio (1775 pacientes): menor mortalidad (OR 0,48; IC 95 % 0,25–0,92) y **más
  sangrado mayor (OR 3,19; IC 95 % 2,07–4,92)**.
- Conclusión de los autores: menor mortalidad total, a costa de más sangrado mayor y más hemorragia intracraneal.
- **Limitaciones:** mezcla fármacos, dosis y épocas; el beneficio de mortalidad fue discutido en cartas
  posteriores. Los porcentajes de hemorragia intracraneal no aparecieron en los extractos, así que no los cito.

### C. ¿Hay fundamento para que la lisis reduzca la obstrucción aunque su uso fuera injustificado?

**Sí, dentro de lo que el simulador modela.** El riesgo intermedio es justamente la población en que la guía no
recomienda la lisis primaria de rutina: su uso ahí no está indicado. Aun así, en los ensayos el fármaco:

- disuelve el trombo y mejora antes el VD y la perfusión (Goldhaber; ESC 2019);
- previene descompensaciones (PEITHO);
- y cobra su precio en sangrado mayor y ACV hemorrágico (PEITHO, Chatterjee).

El efecto farmacológico no depende de la indicación; lo que depende de ella es el balance.

Dos límites:

- **Sin TEP no hay trombo que disolver.** Una lisis injustificada porque el diagnóstico es otro no aplica aquí,
  porque la lisis sólo existe en los casos TEP.
- **El motor no modela la hemorragia intracraneal.** Modela la pérdida oculta y, si el caso declara un sitio (la
  33f, operada hace 12 días), el sangrado de ese sitio. La HIC quedaría como límite declarado.

### Qué hace hoy el motor

`pe_obstruction.lysis_effect` devuelve 0 si la lisis no estaba indicada. La obstrucción no cambia y la sala dice
«the obstruction is unchanged». El sangrado sí ocurre:

- una pérdida oculta de hemoglobina;
- en la 33f, además, el sangrado del sitio quirúrgico desde el minuto 20.

### Opciones

- **A. Mantener:** «daño sin beneficio». Contradice la evidencia (A y C).
- **B. Disolver como cuando está indicada y conservar todo el sangrado.** Es consistente con A, B y C. El juicio
  de la decisión queda donde está:
  - D3 y C1;
  - el evento `pe_unindicated_thrombolysis`, que el tamizaje decide con el registro de indicación de la primera
    dosis, sin cambios.

### P-04 · Recomendación verificada: **B**

La evidencia sostiene que una lisis no indicada reduce la obstrucción y aumenta el sangrado.

**Si usted la aprueba, se implementaría así:**

1. Quitar la condición de indicación en `lysis_effect`.
2. Cambiar la nota de la sala, en inglés y español, para que diga que la obstrucción cede (el fármaco actúa haya o
   no indicación) y que el riesgo de sangrado se tomó sin ella.
3. Registrar la corrección y probar las trayectorias de la 33f.
4. Aplicarla sólo a encuentros nuevos.
5. Agregar a los límites declarados que la HIC no se modela.

La magnitud de la disolución es la misma de enseñanza que ya usa la lisis indicada. Para una paciente normotensa,
el beneficio que se verá es modesto (oxigenación, frecuencia), como en los ensayos.

## P-05 · Una segunda dosis de trombolítico sistémico

1. **¿Hay evidencia clínica razonable?** Escasa. La principal es un registro prospectivo de un solo centro:
   **Meneveau y cols.** (*Chest* 2006;129:1043-50).
   - **Diseño:** de 488 TEP masivos trombolizados, 40 no respondieron (inestabilidad clínica persistente más
     disfunción del VD residual en ecocardiograma a las 36 h). 14 recibieron embolectomía quirúrgica de rescate y
     26 una trombólisis repetida.
   - **Resultados**, con la repetición frente a la cirugía:
     - estancia sin complicaciones: 31 % frente a 79 % (p = 0,004);
     - recurrencia de TEP: 35 % frente a 0 % (p = 0,015);
     - muertes: 10 frente a 1 (p = 0,07).
   - **Limitaciones:** no aleatorizado, pequeño, un centro, sólo TEP masivo y con sesgo de selección. Los datos de
     sangrado no aparecieron en los extractos.
   - Aparte de este registro, hay reportes de casos (por ejemplo, lisis secuencial por trombo en tránsito).
2. **¿Cuándo se usa?** Ante el fracaso de una primera lisis en TEP de alto riesgo, sobre todo donde no hay cirugía
   ni tratamiento por catéter. La guía ESC 2019 recomienda, cuando la trombólisis fracasa o está contraindicada:
   - embolectomía quirúrgica (clase I);
   - tratamiento percutáneo por catéter (clase IIa).

   No recomienda repetir la lisis sistémica. Esto se verificó en el resumen del ACC.
3. **¿Beneficio adicional?** No hay evidencia. El único registro comparativo sugiere peor evolución que el
   rescate quirúrgico, aunque con confusión.
4. **¿Más sangrado?** La dirección es plausible y tiene apoyo indirecto: el sangrado crece con la dosis. Wang 2010:
   - 50 mg frente a 100 mg de alteplasa: sangrado 3 % frente a 10 %;
   - en pacientes de 65 kg o menos: 14,8 % frente a 41,2 % (p = 0,049).

   No hay datos directos del sangrado de una segunda dosis plena en TEP.
5. **¿Fundamento para una relación cuantitativa?** **No.** Ninguna fuente permite decir cuánto sangra una segunda
   dosis. «Exactamente un sangrado completo más» sería una simplificación arbitraria, como usted anticipó.
6. **¿Abstracción cualitativa?** Es la más defendible.

### Modelos comparados

| Modelo | Reperfusión adicional | Sangrado adicional | Evidencia |
|---|---|---|---|
| **A.** Sin efecto (hoy) | No | No | Contradice la dirección del riesgo: enseña que repetir es inocuo |
| **B.** Sin reperfusión adicional + sangrado adicional | No | Sí, con una magnitud | Dirección correcta, pero sin magnitud respaldada |
| **C.** Reperfusión + sangrado adicionales | Sí | Sí | Sin evidencia de beneficio adicional; el registro sugiere lo contrario |
| **D.** Sin reperfusión adicional + riesgo de sangrado aumentado **cualitativo** | No | Declarado y juzgado, sin magnitud fisiológica inventada | Coincide con lo que la evidencia sí sostiene |

### P-05 · Recomendación verificada: **D, cualitativa**

La segunda dosis no agrega disolución, y el aviso de la sala dice lo que la evidencia sostiene:

- no hay beneficio adicional demostrado;
- el riesgo de sangrado aumenta;
- ante una lisis fallida, la guía recomienda cirugía o tratamiento por catéter, no repetir la lisis sistémica.

La decisión la juzgan D3 y C1, y el docente en la revisión de seguridad. La fisiología no agrega un sangrado con
una magnitud que nadie respalda.

Si usted quiere que la paciente **muestre** el sangrado adicional, eso sería B con un **parámetro de enseñanza**
que usted fije, declarado como tal. El motor del TEP ya rotula sus magnitudes como «de enseñanza, pendientes de
revisión docente». Un evento de seguridad propio para la segunda dosis sería otra decisión, que no está en este
alcance.

## Fuentes

- [PEITHO, NEJM 2014](https://www.nejm.org/doi/full/10.1056/NEJMoa1302097) ·
  [PubMed 24716681](https://pubmed.ncbi.nlm.nih.gov/24716681/) ·
  [ACC, resumen del ensayo](https://www.acc.org/Latest-in-Cardiology/Clinical-Trials/2014/04/20/15/26/PEITHO) ·
  [The Bottom Line](https://www.thebottomline.org.uk/summaries/icm/peitho/)
- [PEITHO, seguimiento largo, JACC 2017](https://www.jacc.org/doi/10.1016/j.jacc.2016.12.039)
- [Chatterjee y cols., JAMA 2014](https://jamanetwork.com/journals/jama/fullarticle/1881311) ·
  [PubMed 24938564](https://pubmed.ncbi.nlm.nih.gov/24938564/)
- [Goldhaber y cols., Lancet 1993](https://www.thelancet.com/journals/lancet/article/PII0140-6736(93)90274-K/fulltext)
- [Guía ESC 2019](https://academic.oup.com/eurheartj/article/41/4/543/5556136) ·
  [resumen del ACC](https://www.acc.org/Latest-in-Cardiology/Articles/2020/07/10/08/44/2019-ESC-Guidelines-for-the-Diagnosis-and-Management-of-Acute-PE)
- [Meneveau y cols., Chest 2006](https://pubmed.ncbi.nlm.nih.gov/16608956)
- [Wang y cols., Chest 2010](https://journal.chestnet.org/article/S0012-3692(10)60061-X/fulltext)
