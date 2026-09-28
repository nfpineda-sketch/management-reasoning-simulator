# Auditoría de brechas del banco de casos · ciclo 5

Ítems docentes **59E · 59F · 59BI · 59BJ · 59BK** · rama `clinical-encounter-v0.13` · 2026-09-28.
Sólo auditoría: no se creó ni se modificó ningún caso, y nada de lo que sigue es un cambio hecho.

**Verificación en el código por la sesión principal** (antes de publicar este
informe):

- Los 6 casos con impresión de entrega o de derivación explícita son los que
  dice G1. Sólo `acs_54m_inferior` está en las familias de R1-07.
- `procedural_sedation` existe en el motor de familias (`family_engine.py:80`).
- El contexto de R2-03 se inyecta desde `cognitive_catalog.py` («… with
  respiratory infection»).
- El sorteo autorado es uniforme por par familia–caso
  (`cognitive_generator.py:59`, `rng.choice(candidates)`).
- El ritmo «Sinus …» de los dos pacientes con FA se deriva de la FC en
  `clinical_cases.py:204-205`.

Las columnas «fuerte / moderado / débil» y las clases son estimaciones de
auditoría: no son declaraciones revisadas.

## Resumen para usted

- El banco (31 casos, 12 familias) está bien declarado (31/31 con D1–D5, 32 eventos críticos distintos), pero es **agudo, adulto y cardiocirculatorio**. 29 de 31 casos llegan con una amenaza vital activa, no hay pediatría ni obstetricia, y `acs` tiene 6 de los 31 casos.
- Las brechas más importantes **no piden casos nuevos: son de asignación**. Los desafíos se asignan por familia, pero lo que los hace observables está en casos concretos, a veces fuera de esas familias. R1-07 lo muestra: sólo 1 de sus 9 casos trae una impresión de entrega, y otros 5 casos que sí la traen están fuera de sus familias.
- **C4** no tiene en el banco ninguna oportunidad declarada de sedación procedural. **R1-03, R1-04 y R2-01** no tienen casos del banco, aunque su contenido ya existe en 8 a 31 casos.
- Redundancia principal: las 4 oclusiones coronarias comparten el mismo camino de manejo, y `acs_61m_posterior` ≈ `acs_52m_de_winter`. También `gi_bleed_57m` ≈ `gi_bleed_72f` salvo en D1.
- De 18 brechas, 8 son **clase A** (declarar por caso o ajustar el sorteo), 2 son B, 4 son C y 4 son D. Ninguna B es urgente.

**Convenciones.**
- **Prioridad:**
  - Alta: afecta hoy la validez de un objetivo habilitado.
  - Media: amplitud de un objetivo habilitado.
  - Baja: ningún objetivo activo lo pide, o el objetivo está deshabilitado.
- **Clases 59F:**
  - A: un caso existente puede cubrirla con un ajuste mínimo.
  - B: un caso nuevo podría ser útil.
  - C: se observa mejor por otra fuente.
  - D: no es prioridad actual.
- **«Declarado»** es lo que el banco declara: C14, las familias de cada desafío y D1–D5.
- **«Estimación de auditoría»** es mi lectura de los datos del caso frente al objetivo. No es una declaración revisada y necesita revisión clínica, como se hizo con C14.
- Juzgo sólo contra los **vínculos activos**. Los 9 PARTIAL inactivos por decisión docente no se usan como exigencia.
- TD1, F1, C1, C3 y C4 siguen bajo la **regla de transición**: son observables en todo encuentro. Por eso aquí sólo se estima el contenido del banco para ellos. El borrador paralelo TD/F/C no existía al cerrar este informe.

---

## 1 · 59E Análisis de brechas

### 1.1 Las seis preguntas, en breve

1. **Objetivos con muy pocas oportunidades.**
   - C4 no tiene ningún caso con sedación procedural (G2).
   - R1-03, R1-04 y R2-01 tienen 0 casos del banco (G3).
   - En C3, la vía aérea definitiva es central en un solo caso (G7).
   - R1-07 trae una impresión de entrega explícita en 1 de 9 casos (G1).
   - R1-05 y R2-03 son los pools más chicos: 4 casos cada uno.
2. **Componentes que nunca aparecen.**
   - En C14: neumotórax guiado por POCUS, derrame pericárdico o taponamiento, y aorta patológica (G6a, G6b).
   - Una decisión vasoactiva exigida (G8).
   - Una taquiarritmia primaria (G9).
   - Un paro como situación de partida (G10).
   - El techo terapéutico como decisión central (G14).
   - La sedación para un procedimiento (G2).
3. **Familias sobrerrepresentadas.**
   - `acs` tiene 6 de 31 casos (19 %). El sorteo autorado es uniforme por variante, así que `acs` es el 75 % del pool de R2-02, el 67 % de R1-07 y el 43 % de R2-04 (G4).
   - Las familias cardiocirculatorias (`acs`, `bradycardia`, `pulmonary_embolism`, `pulmonary_edema`) suman 14 de 31 casos.
4. **Familias o contextos ausentes**, juzgados contra lo que piden los objetivos (G9–G17):
   - Pediatría y obstetricia: ningún vínculo activo las pide. `objectives.TARGET_SOURCE` ya declara que las condiciones pediátricas de la guía no se reproducen.
   - Toxicología más allá de opioides: **sí existe** (bloqueo del calcio, betabloqueo, sulfonilurea, alcohol y ayuno).
   - Sepsis: hay 3 casos en 2 familias. Falta la decisión vasoactiva, no más focos.
5. **Dependencia de una sola familia.**
   - R2-02 depende de `acs`.
   - En R2-03, la discordancia sólo existe en `pulmonary_embolism`.
   - En R1-07, el elemento explícito existe en un solo caso.
   - Cada componente de C14 vive en una familia: pared regional sólo en SCA, VD y TVP sólo en TEP, E-FAST sólo en trauma, y congestión sólo en edema pulmonar.
   - La vía aérea definitiva de C3 depende de `asthma_49m`.
   - C2 (deshabilitado) depende de trauma.
   - El año 3 tiene un único desafío (R3-01).
6. **Oportunidades provocadas artificialmente.**
   - R2-03: el contexto «turno con infecciones respiratorias» se inyecta en todo encuentro de ese desafío, y es concordante con el diagnóstico en 2 de sus 4 casos (G5).
   - `hypoglycemia_54m_thiamine`: la vía con que llega no está en la vena y no se ve antes de usarla. Es la única fuente del banco para «comprobar lo que llegó al paciente».
   - Asma: el neumotórax sólo aparece tras presiones meseta altas, y su evento ya nombra el diagnóstico (decisión D).
   - `obstructive_pyelonephritis_58f` es C14 YES, pero el POCUS repetido no está modelado.
   - Por el sorteo por familia, en unos 8 de 9 encuentros de R1-07 y 3 de 14 de R2-04 la oportunidad la pone la etiqueta del desafío, no el caso.

### 1.2 Tabla de brechas (con su clase 59F)

| ID | Objetivo / componente | Oportunidades actuales en el banco | Por qué importa | Familia que podría hacer falta | Prioridad | Recomendación | Clase |
|---|---|---|---|---|---|---|---|
| G1 | **R1-07** · impresión de entrega que contrastar (y COM 2.3) | Pool de 9 casos (`acs` 6, `hypoglycemia` 3). Impresión explícita: 1 (`acs_54m_inferior`, C14 sin revisar por la contradicción VD/POCUS). Encuadre implícito posible: 2 (`hypoglycemia_28m`, `_54m_thiamine`). Con impresión explícita pero **fuera del pool**: `pneumonia_83m`, `pulmonary_embolism_33f`, `asthma_49m`, `anaphylaxis_63m_betablocked`, `bradycardia_ccb_68m`. | La oportunidad que define R1-07 («a supplied handover impression…») falta en unos 8 de 9 sorteos. | Ninguna nueva | **Alta** | Declarar R1-07 por caso (bloque `objectives`, como C14) en los 6 casos con impresión autorada, lo que permite la observación incidental (D-6). Decidir si el encuadre implícito de hipoglicemia cuenta. | **A** |
| G2 | **C4** · sedación y analgesia procedural | 0 declaradas. Analgesia no procedural: `renal_colic_34m`. Procedimientos dolorosos sin analgesia declarada: marcapaso transcutáneo (`bradycardia_avb3_78f`), drenaje pleural (`trauma_hemothorax_41m`, dolor 7) y torniquete en shock (`trauma_limb_hemorrhage_27m`, dolor 8). El motor de familias ya ejecuta `procedural_sedation` con efecto sobre la PA. | C4 está habilitado (meta 20) y la transición lo cuenta como observable en todo encuentro, aunque el banco casi no lo ofrece. Su propia limitación habla de «a limited sedation context». | Opcional: taquiarritmia inestable con cardioversión (G9) | **Alta** | Revisar clínicamente los 3 procedimientos. Si corresponden, declarar C4 con su componente: elegir agente y dosis en hipotensión, anticipar el efecto y reevaluar. Antes, verificar que el motor de cada familia responda. Las destrezas manuales quedan en C. | **A** (+B, C) |
| G3 | **R1-03 · R1-04 · R2-01** (desafíos fundacionales) | 0 casos del banco, porque no tienen familias. El contenido ya está presente: **R1-04**, D4 exige reevaluar la respuesta en 31/31 casos. **R2-01**, PAS ≥90 con perfusión alterada en 8 casos, más 5 casos donde la frecuencia limita el flujo (4 bradicardias y `anaphylaxis_63m_betablocked`, en shock sin taquicardia compensatoria). **R1-03**, taquicardia sinusal compensatoria (FC ≥110) en 15 casos. | Son tres objetivos activos sin ninguna fuente revisada en el banco. Sus encuentros autorados vienen de un escenario único fuera del banco, y tampoco pueden dirigirse a un caso del banco. | Ninguna para R1-04 y R2-01. Para R1-03, una taquiarritmia primaria si la facultad la exige. | **Alta** | Declarar por caso donde el componente sea real, empezando por R1-04 y R2-01. Decidir si la taquicardia sinusal compensatoria satisface R1-03. | **A** (R1-03: A/B) |
| G4 | Sobrerrepresentación de `acs` en R2-02, R1-07 y R2-04 | `acs` tiene 6/31 casos: 75 %, 67 % y 43 % de esos pools. Sus 4 variantes de oclusión siguen el mismo camino de manejo. | Quien entra a R2-02 recibe un SCA 3 de cada 4 veces. La variedad es de ECG (D2), no de manejo. | Ninguna | Media | Sortear primero la familia y luego la variante, o contar las 4 oclusiones como un solo cupo. No retirar casos. | **A** |
| G5 | **R2-03** · contexto de disponibilidad | Pool de 4 casos con un único contexto («infección respiratoria»). Es discordante en `pulmonary_embolism_33f` y `_61m`, y concordante en `pneumonia_46f` y `_83m`. | En los casos concordantes no hay diferencia que distinguir. La pregunta de debrief «What distinguished this patient…» queda sin respuesta clínica. | Ninguna | Media | Decidir si los casos concordantes son controles intencionales. Si no lo son, limitar R2-03 a los discordantes o dar a cada caso su propio contexto. | **A** |
| G6a | **C14** · neumotórax guiado por POCUS | 0. En asma aparece tras ventilación, y el evento ya lo nombra (decisión D). | Las propias declaraciones C14 lo citan como un estado de la EPA, y la meta de C14 es 50. | Ninguna | Media | Rediseñar el evento del asma para que el POCUS encuentre el neumotórax antes de nombrarlo. La decisión D ya lo dejó como una decisión de caso aparte. | **A** |
| G6b | **C14** · derrame pericárdico o taponamiento; aorta | 0 | Mismo motivo que G6a. Además, el taponamiento es un shock obstructivo, y hoy hay un solo caso obstructivo (`pulmonary_embolism_61m`). | Caso con taponamiento, traumático o médico | Media-baja | Es la única brecha de C14 que exige un caso nuevo, si la facultad quiere ampliar C14 o C1. | **B** |
| G7 | **C3** · vía aérea definitiva | Intubación central en 1 caso (`asthma_49m`). Intubación opcional en `opioid_35m` y `_67f`. VMNI en 3 casos. `anaphylaxis_29f` tiene estridor pero ninguna acción de vía aérea declarada. | Hay una sola fuente para «preparar la vía aérea», y la meta de C3 es 20. | Ninguna | Media | Revisar si `anaphylaxis_29f` (vía aérea superior) y los opioides ofrecen C3 real, y declararlo. Coordinar con el borrador TD/F/C. | **A** |
| G8 | **C1/F1** · decisión vasoactiva (vasopresor o inótropo) | 14 casos con perfusión alterada. El vasopresor sólo aparece como alternativa (pielonefritis) o dentro del razonamiento C14 (neumonías). No hay shock cardiogénico franco. | Revisar el modelo de trabajo cuando el volumen no basta es el núcleo de C1, R2-01 y R3-01. | Ninguna | Media | Verificar en el motor si la respuesta a volumen de `pneumonia_46f` o de la pielonefritis deja espacio a esa decisión. Si lo deja, declararla. Si no, la facultad decide si se ajusta. | **A** |
| G9 | Taquiarritmia primaria (FA rápida, TSV, TV) | 0. La FA sólo aparece como antecedente en 2 casos. | Daría a R1-03 una fuente en el banco, a C4 un segundo contexto (cardioversión con sedación), y sumaría a C1. | Taquiarritmia inestable | Media | Es el único caso nuevo que sirve a varios objetivos a la vez. Conviene sólo si G2 y G3 no se resuelven con A. | **B** |
| G10 | Paro o periparo como situación de partida | 0. El motor produce un paro sólo como consecuencia del manejo. | F1 y C1 lo incluyen, pero el ACLS se entrena mejor en simulación de alta fidelidad. | — | Baja | Mantenerlo fuera del banco. | **C** |
| G11 | Pediatría | 0 (la menor edad es 24). | La guía de la EPA pide presentaciones pediátricas; `TARGET_SOURCE` ya declara que no se reproducen, y el motor está calibrado para adultos (70 kg). | Pediátrica | Baja | Observación clínica directa. Mantener la limitación explícita. | **C** |
| G12 | Obstetricia o embarazo | 0. Ninguna mujer en edad fértil tiene estado de embarazo autorado. | Ningún vínculo activo lo pide. | — | Baja | Sólo decidir qué responde el caso si alguien pregunta (ver decisiones). | **D** |
| G13 | Urgencias neurológicas primarias (ACV, estado epiléptico, HIC, meningitis) | 0. Hay 9 casos con conciencia alterada por causas metabólicas, tóxicas, sépticas, hipercápnicas o de bajo flujo, y `hypoglycemia_28m` simula un ACV. | Los vínculos activos no lo exigen. C1 declara que no cubre «the full breadth of critical illness». | Neurológica | Baja | No es prioritario. Sería la primera familia a considerar si se amplían C1 o C3. | **D** |
| G14 | Persona mayor frágil y techo terapéutico | 9 casos ≥65 años y 1 ≥80. El techo terapéutico sólo aparece como alternativa aceptable. | La conversación sobre objetivos de cuidado es C15, que está deshabilitado. | — | Baja | Observación directa o paciente estandarizado. | **C** |
| G15 | Escenarios centrados en la comunicación | Sólo COM 2.3 está vinculado (R1-07). Hay historia colateral en 11 casos. | La interfaz de texto observa poco la comunicación. | — | Baja | Paciente estandarizado u observación directa. | **C** |
| G16 | **C2** · amplitud de trauma | 2 mecanismos (extremidad y hemotórax) en 2 hombres de 27 y 41 años. No hay TEC, pelvis, neumotórax a tensión, vía aérea, quemaduras ni paciente anticoagulado. | C2 está deshabilitado precisamente por su amplitud. | Variantes de trauma | Baja (ahora) | Reevaluarlo sólo si se decide habilitar C2. | **D** |
| G17 | **C15** · fin de vida | 0 casos; el objetivo está deshabilitado. | — | — | Baja | Mantenerlo deshabilitado. | **D** |

---

## 2 · 59F Clasificación

| Clase | Brechas | Lectura |
|---|---|---|
| **A** · un caso existente puede cubrirla | G1, G2, G3, G4, G5, G6a, G7, G8 | 8 de 18. Casi todo es de **declaración o de sorteo**, no de contenido. |
| **B** · un caso nuevo podría ser útil | G6b, G9 (y R1-03, si se exige una taquiarritmia) | 2. Ninguna es urgente, y G9 sólo conviene si G2 y G3 no se resuelven con A. |
| **C** · mejor por otra fuente | G10, G11, G14, G15 (más las destrezas manuales de C3 y C4) | 4 |
| **D** · no es prioridad actual | G12, G13, G16, G17 | 4 |

**Ajustes mínimos de clase A** (sólo descritos, no implementados):

- **A1 · Declaración por caso** (G1, G2, G3, G7). Es el mismo mecanismo que C14: `yes` o `no` con su razón, el componente observable, la evidencia esperada y la revisión firmada. `observation_opportunities` ya acepta declaraciones de cualquier objetivo y la observación incidental (D-6). Esto corrige el desfase entre familia y caso sin mover ningún caso de familia.
- **A2 · Sorteo autorado familia → variante** (G4). Es un cambio de ingeniería, no clínico.
- **A3 · Contexto de R2-03** (G5). Restringirlo a los casos discordantes, o darle a cada caso su propio contexto.
- **A4 · Evento del neumotórax del asma** (G6a). Ya estaba señalado en la decisión D.
- **A5 · Verificar el motor antes de declarar** (G2, G8). Comprobar el efecto hemodinámico de la sedación en `bradycardia` y `trauma`, y la respuesta a volumen en la sepsis.

---

## 3 · 59BI Diversidad del banco

| Dimensión | Distribución (31 casos) | Observación |
|---|---|---|
| Edad | <18: **0** · 18–34: 6 · 35–49: 5 · 50–64: 11 · 65–79: 8 · ≥80: **1**. Mediana 57 (rango 24–83). | No hay pediatría. Hay una sola persona ≥80 (`pneumonia_83m`). |
| Sexo | 18 hombres / 13 mujeres | Trauma: 2/2 hombres. Los 3 patrones de oclusión «ocultos» (posterior, de Winter, Wellens) son todos hombres. |
| Comorbilidades | 0: 3 · 1: 11 · 2: 16 · 3: 1. HTA 10, ERC 5, DM2 5 (+ DM1 1), FA 2, asma 2. Cáncer, inmunosupresión, alcohol, diálisis e ICFEr: 1 cada uno. | No hay EPOC, demencia, fragilidad declarada ni embarazo. La anticoagulación nunca pesa en el manejo (el apixabán de `anaphylaxis_63m` no tiene papel). |
| Peso y talla | Peso 47–122 kg (mediana 77). IMC 19,4–45,4 (mediana 29,0). IMC ≥30: 12; ≥40: 2; <18,5: 0. 16/31 casos con peso real ≥1,3 × el ideal. Forma de obtención: medido 13, referido 15, estimado 3. | El peso seco de `bradycardia_hyperk_63m` sigue sin definir (pendiente docente). |
| Agudeza | Perfusión alterada 14 (+3 leve) · PAS <90: 9 · índice de shock ≥1: 11 · SpO₂ <90: 8 · conciencia alterada: 9 · fiebre ≥38: 2 | **29/31 llegan con una amenaza vital activa.** Sin amenaza vital activa: 2 (Wellens y el cólico no complicado). |
| Tipo de shock | Hemorrágico 4 · distributivo 5 (séptico 3, anafiláctico 2) · obstructivo 1 · bradicárdico 4 (3 tóxicos o metabólicos, 1 bloqueo AV) · cardiogénico sólo limítrofe (`acs_70f_left_main`, `acs_54m_inferior`) | No hay taponamiento, neumotórax a tensión ni shock cardiogénico franco. |
| Disposición esperada (lectura de D5) | Alta como decisión central: **1** (`renal_colic_34m`) · alta posible tras observación: 4 · observación o ingreso monitorizado: 6 · nivel crítico según la respuesta: 8 · terapia definitiva que el motor no ejecuta (reperfusión, cirugía, diálisis, marcapaso, descompresión): **12** · paliativo o techo: **0** | Hay 5 eventos de «alta insegura». |
| Fuente de la historia | Paciente: 20 · colateral: 11 · impresión de entrega explícita: 6 | — |
| Idiomas | Inglés: 31/31. Español: borrador completo en 31/31, sin pasajes faltantes ni desactualizados (`tools_case_text.problems()`). | La aprobación caso a caso vive en la base del despliegue y no se ve en las fuentes. Las filas de C14 existen sólo en inglés. |
| Pediatría / obstetricia | 0 / 0 | — |
| Piloto de validación (6 casos) | `asthma_24f`, `pneumonia_46f`, `gi_bleed_57m`, `anaphylaxis_29f`, `renal_colic_34m`, `trauma_limb_hemorrhage_27m`. 3 mujeres / 3 hombres, 24–57 años. | Nadie ≥65 años, sin historia colateral, sin impresión de entrega, sin SCA ni tóxicos. 3/6 son C14 YES. Incluye el único caso de alta. |

---

## 4 · 59BJ Redundancia

| Grupo | Qué comparten | Qué añade cada uno | Juicio |
|---|---|---|---|
| `acs_61m_posterior` ↔ `acs_52m_de_winter` | Mismo camino del motor (oclusión activa, sin VD, ICP disponible, hemodinamia estable). Mismas acciones (aspirina, consulta, reperfusión). **D1, D2, D4 y D5 idénticos.** Mismos 2 eventos críticos. Mismo componente C14 (decisión A). | Posterior: derivaciones posteriores e imagen en espejo. De Winter: patrón que precede al ST, con 40 minutos de evolución. | **Casi duplicados en el manejo.** Se distinguen sólo en la interpretación del ECG. |
| Las 4 oclusiones (las 2 anteriores + `acs_54m_inferior`, `acs_70f_left_main`) | D1, D2, D4 y D5 idénticos; mismas acciones y eventos. | Inferior: compromiso del VD, bradicardia, riesgo del nitrato y encuadre «¿indigestión?». Tronco común: hipoperfusión y congestión (decisión de volumen y soporte). | Complementarias: estas dos sí añaden decisiones propias. |
| `acs_66f_nonst`, `acs_48m_wellens` | D1, D2, D4 y los eventos, iguales que el resto del SCA | NSTE: destino monitorizado sin cateterismo inmediato. Wellens: paciente que se ve bien, no hacer prueba de provocación, no dar el alta. | Complementarios |
| `gi_bleed_57m` ↔ `gi_bleed_72f` | Misma etiología (AINE), melena, Hb 6,7/6,4, mismas acciones y evento, **D2–D5 idénticos**, mismo componente C14 | 57m: shock evidente. 72f: presentación silenciosa en una persona mayor. | **Casi duplicados salvo D1.** El valor propio de 72f sirve a R2-04 y R2-01, a los que `gi_bleed` no está asignada. |
| `pneumonia_46f` ↔ `pneumonia_83m` | Mismas acciones; D3–D5 y componente C14 idénticos | 83m: delirium, derivación «¿deshidratación?» y un evento propio. 46f: el metotrexato no se usa en ninguna declaración. | Redundancia moderada: 46f aporta poco propio. |
| `opioid_35m` ↔ `opioid_67f` | Mismas acciones y D2–D4. Ambos tratan de «no dar el alta tras la primera respuesta». | 35m: comprimido desconocido que aún se absorbe. 67f: opioide de acción prolongada, ERC y evento de alta insegura. | Moderada; es un contraste deliberado de D5. |
| `bradycardia_ccb_68m` ↔ `bradycardia_bb_54f` | Mismas acciones (con el orden de los antídotos invertido), mismos eventos, D1/D4/D5 idénticos y el mismo POCUS (compartido también con `_hyperk_63m`) | Discriminar el tóxico por la glucosa; en 54f, intención autolesiva. | Par de contraste deliberado: mantener. El POCUS idéntico no afecta, porque C14 es NO. |
| Edema pulmonar, TEP, asma, anafilaxia, cólico/pielonefritis, trauma, hipoglicemia | — | Cada par separa una decisión distinta. | No son redundantes. |

**Entre familias**, por diseño y sin problema:
- «No dar el alta tras la respuesta inicial» aparece en 4 casos (R1-06).
- «Sangre antes que cristaloide» aparece en 4 casos (HDA y trauma).
- «Volumen guiado por POCUS en sepsis» aparece en 3 casos, con el mismo componente C14.

---

## 5 · 59BK Cobertura de los Decision Challenges

Las columnas «fuerte / moderado / débil» son estimación de auditoría y requieren revisión clínica.

| Desafío | Año | Familias | Casos | Familia mayor | Elemento en el caso: fuerte / moderado / débil | Dependencia | Casos fuera del pool que ya lo contienen |
|---|---|---|---|---|---|---|---|
| R1-05 anclaje | 1 | `pneumonia`, `pulmonary_edema` | 4 | 50 % | 2 (`pneumonia_83m`, `pulmonary_edema_58m`) / 1 / 1 (`pneumonia_46f`) | Sólo respiratorias | `gi_bleed_72f`, `pulmonary_embolism_33f`, `acs_54m_inferior`, `asthma_49m` |
| R1-06 cierre prematuro | 1 | `hypoglycemia`, `opioid`, `anaphylaxis` | 7 | 43 % | 4 (76f, `opioid_67f`, `anaphylaxis_29f`, `opioid_35m`) / 2 / 1 (`hypoglycemia_28m`) | Ninguna | `bradycardia_hyperk_63m`, bradicardias tóxicas |
| R1-07 encuadre | 1 | `acs`, `hypoglycemia` | 9 | 67 % | **1 explícito** (`acs_54m_inferior`) / 2 implícitos / 6 sin elemento | **De hecho, un solo caso** | `pneumonia_83m`, `pulmonary_embolism_33f`, `asthma_49m`, `anaphylaxis_63m_betablocked`, `bradycardia_ccb_68m` |
| R2-02 confirmación | 2 | `acs`, `pulmonary_embolism` | 8 | **75 %** | 5 / 3 / 0 | `acs` | `pneumonia_83m`, cólico vs. pielonefritis, bradicardias tóxicas |
| R2-03 disponibilidad | 2 | `pulmonary_embolism`, `pneumonia` | 4 | 50 % | 2 discordantes / — / 2 concordantes | TEP (para la discordancia) | — (el contexto se inyecta) |
| R2-04 representatividad | 2 | `acs`, `pulmonary_embolism`, `bradycardia`, `trauma` | 14 | 43 % | 9 / 2 / 3 (`acs_66f_nonst`, `bradycardia_avb3_78f`, `trauma_limb_hemorrhage_27m`) | Ninguna | `pneumonia_83m`, `gi_bleed_72f`, `hypoglycemia_28m` |
| R2-05 satisfacción de búsqueda | 2 | `gi_bleed`, `pneumonia`, `renal_colic`, `trauma` | 8 | 25 % | 3 (pielonefritis, hemotórax, `pneumonia_83m`) / 3 / 2 (`renal_colic_34m`, `trauma_limb_hemorrhage_27m`) | Ninguna | `bradycardia_hyperk_63m`, `pulmonary_embolism_61m` |
| R3-01 sesgo de acción | 3 | `pulmonary_edema`, `asthma`, `anaphylaxis` | 6 | 33 % | 3 / 3 / 0 | Ninguna, pero es el **único desafío de año 3** | `pulmonary_embolism_33f` (trombólisis no indicada), bradicardias (atropina repetida), `trauma_limb_hemorrhage_27m` (cristaloide) |
| **R1-03** | 1 | — | **0** | — | Candidatos: 15 casos con taquicardia sinusal compensatoria | Encuentros fuera del banco | — |
| **R1-04** | 1 | — | **0** | — | Candidatos: 31/31 (D4 exige comprobar la respuesta) | Ídem | — |
| **R2-01** | 2 | — | **0** | — | Candidatos: 8 con discordancia presión–perfusión, más 5 con flujo limitado por la frecuencia | Ídem | — |

**Titular.**
- Los 8 desafíos con familias sortean entre 4 y 14 casos del banco. Las 12 familias sirven al menos a un desafío, y ningún desafío depende formalmente de una sola familia.
- El contenido real **por caso** es más delgado que el pool:
  - R1-07 tiene su elemento explícito en 1 de 9 casos.
  - R2-03 es discordante sólo en 2 de 4.
  - R2-02 es SCA en un 75 %.
- Los casos con más valor diferencial (`pneumonia_83m`, `gi_bleed_72f`, `pulmonary_embolism_33f`) están en familias que no están asignadas a los desafíos que mejor servirían.
- R1-03, R1-04 y R2-01 no tienen casos del banco, aunque su componente ya existe en 8 a 31 casos.

---

## Qué requiere decisión docente

1. **R1-07.** ¿Se declara R1-07 por caso en los 6 casos con impresión de entrega autorada? ¿Cuenta el encuadre implícito de `hypoglycemia_28m` y `_54m_thiamine`? Tenga en cuenta que el único caso explícito del pool, `acs_54m_inferior`, sigue pendiente por la contradicción VD/POCUS.
2. **C4.** ¿Cuentan como C4 la analgesia o sedación del marcapaso transcutáneo, del drenaje pleural y del torniquete? ¿Cuenta la analgesia del cólico, que no es procedural?
3. **Desafíos fundacionales.**
   - ¿Se abren R1-04 y R2-01 a casos del banco mediante declaración por caso?
   - ¿La taquicardia sinusal compensatoria satisface R1-03, o se exige una taquiarritmia primaria (G9, clase B)?
4. **Sorteo.** ¿Se sortea primero la familia y luego la variante, para que `acs` no domine R2-02, R1-07 y R2-04? ¿Las 4 oclusiones cuentan como un solo cupo?
5. **R2-03.** ¿Los casos concordantes (las neumonías) son controles deliberados?
6. **C14.** ¿Se rediseña el evento del neumotórax del asma (decisión D)? ¿Se busca un caso con estado pericárdico (G6b)?
7. **Decisión vasoactiva.** ¿Debe algún caso séptico exigirla? Antes hay que verificarlo en el motor.
8. **Alcance.** Confirmar que pediatría, obstetricia, fin de vida y comunicación quedan fuera del simulador (clases C y D), y que así se declara.
9. **Observaciones incidentales** (no son brechas; están por verificar):
   - `anaphylaxis_63m_betablocked` y `bradycardia_ccb_68m` tienen FA como antecedente, pero su ritmo de llegada se rotula «Sinus …», derivado de la FC.
   - Ninguna mujer en edad fértil tiene estado de embarazo autorado. Es relevante para `pulmonary_embolism_33f` antes de la angio-TC: ¿qué responde el caso si alguien pregunta?
10. **Piloto.** Sus 6 casos no incluyen a nadie ≥65 años, ni historia colateral, ni impresión de entrega. ¿Es aceptable para lo que el piloto valida?

---

### Fuentes y límites

- **Fuentes leídas:**
  - `clinical_cases.py`, `case_assessment_bank.py` y `observation_opportunities.py`.
  - `objectives.py`, `competency_mapping.py`, y `curriculum.py` con `cognitive_catalog.py`, que define `CHALLENGES`, sus familias y el contexto de R2-03.
  - `patient_body.py` y `validation_corpus.PILOT_CASES`.
  - `docs/C14_TABLA_FINAL.md` y `docs/COBERTURA_CASOS.md`.
- **Consultados sólo para confirmar mecanismos:**
  - `cognitive_generator.py`: sorteo uniforme por variante.
  - `encounter_generator.py` y `encounter_directives.py`: origen de R1-03, R1-04 y R2-01, y ausencia de casos dirigibles para ellos.
  - `hypoglycemia_catalog.py`: narrativa de los 3 casos de hipoglicemia.
  - `family_engine.py`: `procedural_sedation` es ejecutable.
  - `tools_case_text.problems()`: completitud del español.
- **Extracción.** Se hizo en modo de solo lectura (`audit_gaps/extract.py` → `bank.json`), sin bytecode y sin escribir en el repositorio.
- **Fuera de alcance.** Los casos generados, que son la vía por defecto de las personas residentes, no están en las fuentes y no se auditan aquí.
