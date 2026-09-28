# Borrador · Oportunidad de observar C14 en los 31 casos del banco

Ciclo 3 del AI Advisor, punto G de la autorización docente del 2026-09-27 (DF-1,
D-5).

**Estado: BORRADOR PARA REVISIÓN CLÍNICA.**

**Ciclo 4 (2026-09-28).** Las dudas se prepararon como ocho decisiones clínicas
en `docs/C14_DECISIONES_A_H.md`: formato A–H, con recomendación, casos
afectados y consecuencias. `c14_review.py` deriva las filas a partir de las
respuestas. Los estados de esta tabla no cambiaron: siguen siendo el borrador
hasta que la docencia responda.

Correcciones factuales de este ciclo, en la última columna de cada fila:

- `acs_54m_inferior`: el VD declarado contradice el POCUS.
- `bradycardia_avb3_78f`: su POCUS no refleja la captura.
- `pulmonary_embolism_33f` y `pulmonary_embolism_61m`: el POCUS trae una TVP
  proximal que el borrador omitía.
- `obstructive_pyelonephritis_58f`: también depende de la pregunta C.
- Ecografía renal: es un estudio aparte, no el POCUS.

- No es metadata aprobada.
- Ningún caso del banco tiene todavía un bloque `objectives`: nada de esta tabla
  está activo. Una prueba lo verifica (`test_observation_opportunities.py`).
- Mientras un caso no se revise, C14 sigue observable en él con la regla de
  transición, como antes (`observation_opportunities.py`).

## Qué se pregunta

**C14 · Use POCUS to guide management.** El alcance local
(`objectives.py`) es: pedir los hallazgos POCUS que el caso entrega,
interpretar su implicancia para el manejo y relacionarlos con las decisiones
siguientes. No observa la adquisición de la imagen ni el manejo del
transductor.

**Criterio del borrador.** Hay oportunidad sólo si un hallazgo POCUS de este
caso puede cambiar o sostener de forma importante una decisión de manejo.

- **Que el POCUS esté disponible no basta.** Los 31 casos lo traen.
- **Estados que lista la EPA C14** (EPA Guide v1.1, p. 42): derrame pericárdico
  y taponamiento, estimación global de la fracción de eyección del VI,
  neumotórax, hemotórax, derrame pleural, aneurisma de aorta abdominal, líquido
  libre abdominal o pélvico, y gestación intrauterina del primer trimestre.
- **Hallazgos fuera de esa lista** (motilidad regional, ventrículo derecho,
  vena cava, consolidación, hidronefrosis) se marcan UNCERTAIN y se remiten a
  una pregunta.

## Resumen

| Borrador | Casos |
|---|---|
| **YES** | 6 |
| **NO** | 6 |
| **UNCERTAIN** | 19 |

Las 19 dudas se reducen a **8 preguntas** (A a H, al final). Cada una resuelve
varios casos a la vez.

## Matriz

| Case ID | Familia | C14 (borrador) | Racional | Componente observable | Evidencia esperable en el Trace | Incertidumbre / nota de revisión |
|---|---|---|---|---|---|---|
| `acs_54m_inferior` | acs | UNCERTAIN | La reperfusión se decide con el ECG. El POCUS muestra hipocinesia inferior y VD normal, y el VD podría orientar nitratos y volumen en un IAM inferior. | Ajustar el manejo del IAM inferior según la contractilidad regional y del VD. | Pide POCUS; nombra hipocinesia inferior y VD normal; lo relaciona con nitratos o volumen. | Pregunta A. **Ciclo 4:** el caso declara compromiso del VD (`rv_involvement`) y el motor lo modela, pero el POCUS escrito dice VD normal: inconsistencia de datos para decisión docente. |
| `acs_66f_nonst` | acs | UNCERTAIN | ECG y troponina deciden. La hipocinesia inferolateral leve apoya la isquemia y podría pesar contra el alta. | Integrar la alteración regional al riesgo y al destino. | Pide POCUS; relaciona la hipocinesia con la troponina; no da de alta. | Pregunta A. |
| `acs_61m_posterior` | acs | UNCERTAIN | IAM posterior con ECG sutil. La hipocinesia posterior apoya tratarlo como equivalente de supradesnivel, junto con las derivaciones posteriores. | Apoyar la decisión de reperfusión con la motilidad regional. | Pide POCUS; nombra la hipocinesia posterior; la usa junto al ECG para activar reperfusión. | Pregunta A. |
| `acs_52m_de_winter` | acs | UNCERTAIN | De Winter se reconoce en el ECG; la acinesia anterior en el POCUS lo apoya. | Apoyar la decisión de reperfusión con la motilidad regional. | Pide POCUS; nombra la acinesia anterior; la relaciona con la reperfusión. | Pregunta A. |
| `acs_48m_wellens` | acs | UNCERTAIN | El POCUS es normal en reposo. El riesgo es tranquilizarse con él; la oportunidad sería observar que no se use para descartar. | Reconocer que un POCUS normal no descarta la lesión. | Si pide POCUS, no lo usa para dar de alta ni para descartar. | Preguntas A y B. |
| `acs_70f_left_main` | acs | **YES** | Presión límite (PAS 104, FC 112, llene 3 s) con contractilidad global disminuida. La estimación global de la FE, un estado que la EPA lista, orienta a no cargar volumen y a anticipar soporte. | Decidir volumen, soporte y urgencia según la función global del VI. | Pide POCUS; nombra la contractilidad global disminuida; limita el volumen o escala el soporte. | Confirmar que la evolución del caso hace decisiva esa elección. |
| `anaphylaxis_29f` | anaphylaxis | UNCERTAIN | Diagnóstico y adrenalina son clínicos. El VI hiperdinámico y la VCI de 0,9 cm colapsable apoyan un shock distributivo con precarga baja. | Guiar la reposición de volumen, junto a la adrenalina, con la valoración de volumen. | Pide POCUS; nombra VI hiperdinámico y VCI colapsada; lo relaciona con el volumen. | Pregunta C. |
| `anaphylaxis_63m_betablocked` | anaphylaxis | UNCERTAIN | Shock refractario (PAS 76) en un paciente betabloqueado, sin patrón hiperdinámico. El glucagón lo orienta la historia; el POCUS apoya. | Relacionar la contractilidad no hiperdinámica con el betabloqueo y el soporte. | Pide POCUS; lo relaciona con el betabloqueo, el glucagón o el volumen. | Pregunta C. |
| `asthma_24f` | asthma | UNCERTAIN | El manejo es broncodilatador y el POCUS es normal, con deslizamiento pleural presente. Guía sólo si el curso pone el neumotórax en el diferencial. | Excluir un neumotórax ante un deterioro, para decidir el manejo. | Ante un deterioro, pide POCUS, nombra el deslizamiento presente y decide con él. | Pregunta D. |
| `asthma_49m` | asthma | UNCERTAIN | Igual, y más grave (somnoliento, SpO₂ 89 %): la intubación, y con ella la pregunta por el neumotórax, es más probable. | Igual. | Igual. | Pregunta D. |
| `bradycardia_ccb_68m` | bradycardia | UNCERTAIN | Bradicardia con shock (PAS 74) por calcioantagonista, con contractilidad global disminuida. Su función del VI orienta el soporte inotrópico o la insulina en dosis alta frente al vasopresor. | Elegir el soporte según la contractilidad. | Pide POCUS; nombra la contractilidad disminuida; elige el soporte en consecuencia. | Pregunta E. |
| `bradycardia_avb3_78f` | bradycardia | UNCERTAIN | Bloqueo completo con shock (PAS 78); la decisión es el marcapaso. El POCUS podría confirmar la captura mecánica. | Confirmar la captura mecánica tras el marcapaso. | Tras el marcapaso, pide POCUS o reevalúa pulso y presión, y lo relaciona. | **Verificado (ciclo 4): no.** El POCUS no cambia tras la captura y seguiría informando la frecuencia lenta. Ahora en la pregunta E. |
| `bradycardia_bb_54f` | bradycardia | UNCERTAIN | Igual que el calcioantagonista, con betabloqueador (PAS 80). | Elegir el soporte según la contractilidad. | Igual. | Pregunta E. |
| `bradycardia_hyperk_63m` | bradycardia | **NO** | Hiperkalemia: calcio, insulina con glucosa y eliminación. El POCUS no cambia el manejo. | — | — | — |
| `gi_bleed_57m` | gi_bleed | UNCERTAIN | Shock hemorrágico (PAS 88): la transfusión y la endoscopia dependen de la clínica. El VI vacío y la VCI colapsada confirman la hipovolemia. | Usar la valoración de volumen como objetivo de la reanimación. | Pide POCUS; nombra VI vacío y VCI colapsada; lo relaciona con la reposición. | Pregunta C. |
| `gi_bleed_72f` | gi_bleed | UNCERTAIN | Igual, con VI hiperdinámico. | Igual. | Igual. | Pregunta C. |
| `hypoglycemia_28m` | hypoglycemia | **NO** | La glicemia capilar y la glucosa resuelven. El POCUS no aporta al manejo. | — | — | — |
| `hypoglycemia_76f` | hypoglycemia | **NO** | Igual. | — | — | — |
| `hypoglycemia_54m_thiamine` | hypoglycemia | **NO** | Igual; la tiamina se decide por la historia. | — | — | — |
| `opioid_35m` | opioid | **NO** | Depresión respiratoria por opioides: naloxona y ventilación. El POCUS no aporta. | — | — | — |
| `opioid_67f` | opioid | **NO** | Igual. | — | — | — |
| `pneumonia_46f` | pneumonia | UNCERTAIN | El antibiótico no depende del POCUS. La consolidación basal derecha apoya el diagnóstico, y el VI normal con VCI colapsable apoya reponer volumen en la sepsis. | Confirmar el foco y guiar los fluidos con el POCUS pulmonar y cardíaco. | Pide POCUS; nombra la consolidación y la VCI; lo relaciona con antibiótico y volumen. | Preguntas C y F. |
| `pneumonia_83m` | pneumonia | UNCERTAIN | Consolidación basal izquierda; la confusión obliga a estudiar además otras causas. | Igual. | Igual. | Preguntas C y F. |
| `pulmonary_edema_58m` | pulmonary_edema | **YES** | Líneas B difusas, VI moderadamente deprimido y VCI pletórica separan la congestión de otras causas. El caso lo pide en D2 y tiene como evento crítico cargar volumen. | Decidir nitratos, diuréticos o VNI, y no dar volumen, según líneas B, función del VI y VCI. | Pide POCUS; nombra líneas B y VI deprimido; evita el volumen; indica nitrato, diurético o VNI. | — |
| `pulmonary_edema_75f` | pulmonary_edema | **YES** | Igual, con VI gravemente deprimido y derrames pleurales pequeños. | Igual. | Igual. | — |
| `pulmonary_embolism_33f` | pulmonary_embolism | UNCERTAIN | Estable (PAS 110). El VD levemente dilatado apoya el diagnóstico, la angioTC decide y la trombólisis no está indicada. | Integrar el VD a la estratificación del riesgo. | Pide POCUS; nombra el VD; lo relaciona con la angioTC y la anticoagulación. | Pregunta G. **Ciclo 4:** el POCUS trae además una TVP poplítea no compresible (TVP proximal) que el borrador omitía; confirma la enfermedad tromboembólica antes de la angioTC. |
| `pulmonary_embolism_61m` | pulmonary_embolism | **YES** | Shock (PAS 86, SpO₂ 88 %) con VD mayor que el VI, signo D y McConnell. El POCUS justifica tratarlo como TEP masivo y considerar trombólisis sin esperar la angioTC. | Decidir la reperfusión según la sobrecarga del VD en shock. | Pide POCUS; nombra VD dilatado y signo D; decide anticoagulación o trombólisis en consecuencia. | El VD no es un estado que la EPA liste. **Ciclo 4:** su SÍ descansa en el VD, así que queda sujeto a la pregunta G; el POCUS trae también una TVP poplítea izquierda. |
| `renal_colic_34m` | renal_colic | UNCERTAIN | El estudio renal muestra una dilatación leve con un cálculo de 5 mm; con la orina y la temperatura separa el cólico de la obstrucción infectada. | Decidir la derivación relacionando la dilatación con la infección. | Pide la ecografía renal; relaciona dilatación, orina y temperatura. | Pregunta H. |
| `obstructive_pyelonephritis_58f` | renal_colic | UNCERTAIN | Obstrucción infectada con sepsis (PAS 94): la dilatación, con la infección, exige descompresión urgente. | Igual. | Pide la ecografía renal; relaciona dilatación y sepsis; pide la descompresión urológica. | Pregunta H. **Ciclo 4:** también pregunta C: shock séptico con VCI de 1,0 cm colapsable, como las neumonías. La ecografía renal es un estudio aparte con informe formal, no el POCUS. |
| `trauma_limb_hemorrhage_27m` | trauma | **YES** | E-FAST negativo en las cinco ventanas, en shock: descarta la cavidad y orienta a la extremidad como fuente compresible. Líquido libre, hemotórax, neumotórax y pericardio son estados que la EPA lista. | Orientar el control de la hemorragia con la ausencia de líquido libre en el E-FAST. | Pide E-FAST; nombra que es negativo; dirige el control a la extremidad y no a la cavidad. | — |
| `trauma_hemothorax_41m` | trauma | **YES** | El E-FAST muestra un derrame pleural izquierdo ecogénico: un hemotórax, estado que la EPA lista, en shock. Define el drenaje, y los eventos críticos del caso son el hemotórax no drenado y no reevaluado. | Decidir el drenaje y su reevaluación con el hallazgo de hemotórax. | Pide E-FAST; nombra el hemotórax izquierdo; indica tubo pleural; reevalúa. | — |

## Preguntas para la revisión

Cada respuesta resuelve los casos que la citan.

| Pregunta | Casos | Qué hay que decidir |
|---|---|---|
| **A** | 5 de SCA | ¿Cuenta como oportunidad C14 usar la motilidad regional y el ventrículo derecho en un síndrome coronario agudo? No son estados que la EPA liste, y la reperfusión la decide el ECG. |
| **B** | Wellens | ¿Cuenta como C14 observar que un POCUS normal no se use para descartar? |
| **C** | anafilaxia ×2, HDA ×2, neumonía ×2 | ¿Cuenta la valoración de volumen (VCI, VI vacío) para guiar fluidos? No es un estado que la EPA liste. |
| **D** | asma ×2 | La oportunidad existe sólo si el curso lleva a sospechar un neumotórax. El esquema no tiene un estado «condicional»: ¿se declara YES, anotando esa condición en la evidencia esperada, o NO? |
| **E** | bradicardias tóxicas ×2 | ¿Cuenta la contractilidad para elegir el soporte? ¿Y el caso responde de distinta forma a esa elección? |
| **F** | neumonía ×2 | ¿Cuenta la consolidación vista con POCUS? |
| **G** | TEP ×2 | ¿Cuenta la sobrecarga del ventrículo derecho? No es un estado que la EPA liste. |
| **H** | renal ×2 | ¿La ecografía renal del caso es POCUS o un estudio formal? ¿Cuenta la hidronefrosis? |

Además, en `bradycardia_avb3_78f` hay que verificar técnicamente si el POCUS
refleja la captura del marcapaso.

## Cómo se activa lo que se apruebe

1. **Registrar el caso aprobado.** Por cada caso aprobado o corregido, se
   escribe la entrada en el bloque `objectives` de su declaración, en
   `case_assessment_bank.py`: estado, racional, componente, evidencia esperable,
   y quién la revisó y cuándo. `case_assessment.verify` la valida.
2. **Sólo encuentros nuevos.** Rige para los encuentros que se inicien después,
   porque la declaración se congela con cada encuentro. Los anteriores no
   cambian.
3. **Casos rechazados o no revisados.** Un caso que diga NO deja C14 fuera de
   sus encuentros nuevos. Uno sin revisar sigue con la regla de transición.

La evidencia esperable orienta: el docente puede reconocer evidencia válida que
no esté en la lista.
