# B-5 · Relato en español · Integridad y completitud de los 30 casos del piloto

> **Comprobación determinista, de sólo lectura (sesión autónoma del 2026-10-08).** Script:
> `integrity30.py` (fuera del repositorio, en el área de trabajo de la sesión); cada cifra de este documento la
> produce el script sobre `case_text/es`, `pilot_freeze.CASES`, `clinical_cases.FAMILIES`, los documentos de lote
> (`docs/revision/B5_RELATO_R*.md`) y el lote 0. No cambia nada del repositorio.

## Resultado

- **Casos del piloto de residentes:** 30 (únicos: sí). El manifiesto tiene 31; excluido: `trauma_hemothorax_41m` (EXCLUDE, sandbox docente), que está en `case_text` (31 casos) pero no cuenta entre los 30.
- **Estado del relato:** 21 aprobados por la docencia, 9 revisados y pendientes de decisión docente, 0 sin revisar. Total 30.
- **Cobertura de los lotes:** cada caso del piloto está en exactamente un documento de lote; duplicados: 0; faltantes: 0; casos ajenos al piloto: 0.
- **Versiones:** cada versión objetivo se reproduce desde el español del repositorio más los cambios decididos (T-1, T-2, T-3 y P-1, 11 pasajes en 10 casos), y coincide con la versión documentada (la aprobada, o la impresa para los 9 pendientes). Reproducidas: 30 de 30.
- **Pasajes:** 1069 en los 30 casos. Español vacío: 0; alineación con el inglés vigente rota: 0; español idéntico al inglés: 0.
- **Cifras distintas entre inglés y español (en las versiones objetivo):** 0.
- **Inglés dentro del español:** 0. La búsqueda de palabras inglesas dio 62 coincidencias, todas la forma española «he» del verbo haber («No he tenido…»); revisadas: ninguna es inglés.
- **Lote 0:** 47 frases, 527 apariciones, el mismo conjunto que las frases comunes del banco (sí); apariciones cuyo español difiere de la frase aprobada: 0.
- **Corpus de la validación externa:** 18 pasajes fijos; ningún cambio decidido toca uno (0); huella SHA-256 de los 18 (caso, ruta, texto): `6d10a03421f641dce34fde381b238907426919573a7135ea8df9af73b369f492`. La prueba `test_validation_corpus.py::test_the_committed_blank_templates_are_what_the_generator_writes` pasa sobre el repositorio de hoy.
- **Terminología en las versiones objetivo:** «crepitaciones» (T-1): 0; «resistencia muscular» (T-2): 0; adjetivo «confuso» del paciente (T-3): 0.
- **«Crushing»:** `acs_52m_de_winter` `/history/chief_complaint/0` «Siento como si me aplastaran el pecho y estoy sudando.»; `anaphylaxis_29f` `/history/chest_pain/0` «Hay una opresión que atraviesa el pecho, pero no un dolor aplastante en el centro.»; `asthma_24f` `/history/chest_pain/0` «La sensación es de pecho apretado al respirar, no un dolor aparte que sea localizado o aplastante.»; `pulmonary_edema_58m` `/history/chest_pain/0` «Siento opresión en el pecho con el esfuerzo de respirar, sin un dolor aparte, aplastante y persistente.»; `pulmonary_embolism_61m` `/history/chest_pain/0` «Hay una molestia leve en el pecho al respirar profundo, sin una presión opresiva sostenida.». «Aplastante» en todos salvo la 61m («presión opresiva sostenida», conservada por decisión docente en R3A).

## Los 30 casos

| Lote | Caso | Estado | Pasajes | Cambios | Versión del repositorio hoy | Versión objetivo | ¿Se reproduce? |
|---|---|---|---|---|---|---|---|
| R1A | `acs_54m_inferior` | Aprobado | 35 | T-2 | `8426f7ca71d9c4cfc8edb49e43944a53e5776f87357a652ab1cfbe2661ceac14` | `e1afcda52d3e3fab6853c2b1bd44bf07c4e6ef04296cdde9f7fe87723a48076a` | sí |
| R1A | `acs_61m_posterior` | Aprobado | 35 | — | `a6311c114d9c4d8cd1c444fd724a0a62cced41d7ccfbb2392ce25773618d1890` | `a6311c114d9c4d8cd1c444fd724a0a62cced41d7ccfbb2392ce25773618d1890` | sí |
| R1A | `acs_66f_nonst` | Aprobado | 35 | T-1 | `7e013ae208a4b34d3b2d61f2994c6285fc3a89714e29f61dac428a894026c7da` | `d64dc72663d6d94f4b919ab8529e2314263cbb010d4de66e52738a1221eb95c1` | sí |
| R1B | `acs_48m_wellens` | Aprobado | 35 | — | `13a569872e3a88cf1f01537ee50544f5057cc21942bd10d4e3b3ba03681ab04d` | `13a569872e3a88cf1f01537ee50544f5057cc21942bd10d4e3b3ba03681ab04d` | sí |
| R1B | `acs_52m_de_winter` | Aprobado | 35 | T-1 | `b881e9ab322e19179fc39e018a5a6e1c9dfbfd4129898151a72d9fefeaef52db` | `daf766118b4ae254ae6fa4261bebb40a96eb3ce6d3a4d92f3048d0f5acdc4056` | sí |
| R1B | `acs_70f_left_main` | Aprobado | 35 | T-1 | `1bd4171c534ae4414be5d4a037d016d1c3b4235ec3ff376d0b78a0b1acaf39c9` | `c94b56ee409f799557c53b017e5144c4c076549426d9a75aaec6cd314bddb552` | sí |
| R2A | `pneumonia_46f` | Aprobado | 35 | T-1, T-2 | `7b5db0dd396d89dafb439790b0c61467738eff577318e5869c0726a83741f3a3` | `d16cb3330fc87b73abb6d2e03eae76b428b4f61c0c33b9848cff27caa22977ca` | sí |
| R2A | `pneumonia_83m` | Aprobado | 34 | T-1 | `0a65e473433ec383d8b29f77951bb03ed0b8350f568dac5076c0e7e5a67687c4` | `45a84e879f0a33e8167bf2de5937d23d7eb8ef4068439f77f162563640cd0c1b` | sí |
| R2A | `pulmonary_edema_58m` | Aprobado | 34 | T-1 | `a76b14a3a9ef944631ef01db471f7ca015860bbaa9261c3b6dd3a8632040c709` | `dffcae29509ba47cbea4b30959c62e9093d6bce2df1099d724495a6238f804ae` | sí |
| R2B | `asthma_24f` | Aprobado | 33 | P-1 | `6471a99e221d09521b1f72410763897cd1a6d4d588fc2f17b196f0fea93556ab` | `844d280d53271a3444adc8293a73f42ec5aac090a08d4af839d5100a5fbc4615` | sí |
| R2B | `asthma_49m` | Aprobado | 33 | — | `6b8cc7770904dce49a87fccc7ff91b4948d06d2c422c825854d0dc722d057540` | `6b8cc7770904dce49a87fccc7ff91b4948d06d2c422c825854d0dc722d057540` | sí |
| R2B | `pulmonary_edema_75f` | Aprobado | 33 | T-1 | `53c936c98a9624bb20a784cb7cc2580c25800697832ae54afe036461d91bfe9f` | `4695ee50cfa00208c0c9fa70b527e7495119392cf279487b72a5880d25d2d06c` | sí |
| R3A | `bradycardia_ccb_68m` | Aprobado | 37 | — | `10b926936212c922ccd2a3ce699c4d87df4f76d4c50e456bbf0c628d3f8932c4` | `10b926936212c922ccd2a3ce699c4d87df4f76d4c50e456bbf0c628d3f8932c4` | sí |
| R3A | `pulmonary_embolism_33f` | Aprobado | 37 | — | `d3a826e9c4679a8944e2a5eb5e174f36ba800ca0c91a48bd7a14f8afbe05e5ab` | `d3a826e9c4679a8944e2a5eb5e174f36ba800ca0c91a48bd7a14f8afbe05e5ab` | sí |
| R3A | `pulmonary_embolism_61m` | Aprobado | 36 | — | `71c15c2b2811acd747993f8bb4e5d6f0cad5083ceaf035655fe7aba055ebd714` | `71c15c2b2811acd747993f8bb4e5d6f0cad5083ceaf035655fe7aba055ebd714` | sí |
| R3B | `bradycardia_avb3_78f` | Aprobado | 36 | — | `677c6278c0afd61dfc0e8c284473e88109b0d6e9e9222f5883555c60b338d3a7` | `677c6278c0afd61dfc0e8c284473e88109b0d6e9e9222f5883555c60b338d3a7` | sí |
| R3B | `bradycardia_bb_54f` | Aprobado | 37 | — | `45310f3bbe2d6151424d8955d4e2d24e8f88f72341670cf164955dbce8a009d9` | `45310f3bbe2d6151424d8955d4e2d24e8f88f72341670cf164955dbce8a009d9` | sí |
| R3B | `bradycardia_hyperk_63m` | Aprobado | 37 | — | `89a347fa21123325e432c3b04970fd23b7218c8b4b41e2b5b0960510ad61b8e8` | `89a347fa21123325e432c3b04970fd23b7218c8b4b41e2b5b0960510ad61b8e8` | sí |
| R4A | `hypoglycemia_28m` | Aprobado | 33 | T-3 | `ba88eb952b3d3b8d7dacace8c71dbf683529d08eb3c3265b2159645b3cbb212a` | `65cae7edde83847fd6641ca77a94b034da1ced9e1228df8894f9cbe09ab61950` | sí |
| R4A | `hypoglycemia_54m_thiamine` | Aprobado | 33 | — | `cbd0c47926b04387966b539cad27acd7de9dbce5d3f2093d560dede738ed608a` | `cbd0c47926b04387966b539cad27acd7de9dbce5d3f2093d560dede738ed608a` | sí |
| R4A | `hypoglycemia_76f` | Aprobado | 33 | — | `a7abad85dad8fdae2263696303b1a207b7f4d0580fe951cb3e47050d787df845` | `a7abad85dad8fdae2263696303b1a207b7f4d0580fe951cb3e47050d787df845` | sí |
| R4B | `opioid_35m` | Revisado, pendiente | 33 | — | `a130f860dd36d35d309fb845cd389aa59551bc6a95643b2324900bc05649ad12` | `a130f860dd36d35d309fb845cd389aa59551bc6a95643b2324900bc05649ad12` | sí |
| R4B | `opioid_67f` | Revisado, pendiente | 33 | — | `6f065b332e31a608efe54e082265f310eeebfff5aecbc06898905faa0aba2568` | `6f065b332e31a608efe54e082265f310eeebfff5aecbc06898905faa0aba2568` | sí |
| R5 | `anaphylaxis_29f` | Revisado, pendiente | 39 | — | `7ea433dc65d28ee292505e42846080aef573ba0175f327179bf696843567a237` | `7ea433dc65d28ee292505e42846080aef573ba0175f327179bf696843567a237` | sí |
| R5 | `anaphylaxis_63m_betablocked` | Revisado, pendiente | 39 | — | `c153cc253f35dc6509d059ec916100362f97c02616eac022c3a66f4a5b266200` | `c153cc253f35dc6509d059ec916100362f97c02616eac022c3a66f4a5b266200` | sí |
| R5 | `gi_bleed_57m` | Revisado, pendiente | 34 | — | `5d758337c68f1c59fea20607c1d65cd939dcf8953a4ff85cc5b1867a7e9abcca` | `5d758337c68f1c59fea20607c1d65cd939dcf8953a4ff85cc5b1867a7e9abcca` | sí |
| R5 | `gi_bleed_72f` | Revisado, pendiente | 34 | — | `9c6d28681ed8084f616d940bfe16d3475aec1a724f656a43f177930b82dd634b` | `9c6d28681ed8084f616d940bfe16d3475aec1a724f656a43f177930b82dd634b` | sí |
| R6 | `obstructive_pyelonephritis_58f` | Revisado, pendiente | 37 | — | `3a98131bf83b59dd084ce0b1a2a9ad8f3d93d404372e81260254a1e9f5c50c65` | `3a98131bf83b59dd084ce0b1a2a9ad8f3d93d404372e81260254a1e9f5c50c65` | sí |
| R6 | `renal_colic_34m` | Revisado, pendiente | 38 | — | `ec65504955b7c09e9028358d829d377d4b7a96f8f3d9246b335d44e333f710fa` | `ec65504955b7c09e9028358d829d377d4b7a96f8f3d9246b335d44e333f710fa` | sí |
| R6 | `trauma_limb_hemorrhage_27m` | Revisado, pendiente | 51 | — | `58187a00974b8795cd1da0d72e99da0e7c65162bfeeca1531da1db19c11536e7` | `58187a00974b8795cd1da0d72e99da0e7c65162bfeeca1531da1db19c11536e7` | sí |

Los 9 pendientes (R4B, R5 y R6) no cambian: su versión objetivo es la del repositorio. Los 21 aprobados ya llevan su decisión en su documento de lote; al implementar, cada uno debe dar exactamente su versión objetivo.
