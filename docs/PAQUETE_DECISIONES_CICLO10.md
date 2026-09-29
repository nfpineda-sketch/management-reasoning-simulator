# Paquete de decisiones y revisiones docentes · ciclo 10

Ciclo 10, tarea C10-02 (2026-09-29). Reúne en un solo lugar todo lo que espera una decisión o una revisión
docente, para que se conteste **en una sola respuesta**, cuando usted pueda. **Nada se decide solo:** hasta su
respuesta todo sigue como está, y lo que su respuesta cambie se implementa después, con sus pruebas.

**Cómo responder:** una línea por decisión, por ejemplo `P-01 A · P-02 A · P-04 B`. «Acepto las
recomendaciones» aplica la recomendada en todas, salvo P-07 (75f) y P-08, que necesitan su juicio o su texto.

**Ya decidido, fuera del paquete:** DC4-F, opción B mínima (aprobada al abrir el ciclo 10; se implementa en
C10-09).

## Decisiones

### P-01 · DC6 · Peso de la tiamina en D3 (hipoglicemia)

- **Hoy:** expectativa secundaria de D3 (cobertura 1.1). Su omisión aislada no hace inadecuada la corrección
  de la glucosa y nunca justifica demorarla. Su peso exacto no está decidido.
- **Opciones:**
  - **A.** Medida complementaria del nivel 3 de D3: su omisión sola no baja D3 de 2.
  - **B.** Requisito para el nivel 2 de D3.
  - **C.** Sin peso en D3: sólo se observa.
- **Recomendación: A.** Premia darla sin castigar lo que importa primero, la glucosa.
- **Evidencia:** `docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md`, DC6.

### P-02 · DC7 · Evaluaciones ya confirmadas de la 54m

- **Hoy:** un encuentro anterior a la cobertura 1.1 conserva la 1.0, con «sin tiamina» como evento crítico
  (−3). Desde la 1.1 ya no es evento.
- **Hecho:** en los datos conocidos no hay ninguna evaluación confirmada de la 54m (la tanda de 20 no la
  incluye), y la base del piloto aún no existe.
- **Opciones:**
  - **A.** No reevaluar nada de oficio. Si aparece una evaluación 1.0 confirmada de la 54m, el docente usa la
    reevaluación explícita, que pide motivo y persona y conserva la original.
  - **B.** Reevaluar de oficio toda evaluación 1.0 de la 54m; requiere construir la pantalla de reevaluación.
- **Recomendación: A.**

### P-03 · DC8 · La vía fallida como oportunidad de D4

- **Hoy:** ventana de 5 a 60 minutos. Se espera recontrolar la glucosa tras la dosis, reconocer que no llegó
  y restituir una vía que sirva. La alternativa aceptada es instalar una vía nueva antes de la primera dosis.
- **Opciones:**
  - **A.** Mantener 5–60 min, sólo en D4.
  - **B.** Mantenerla en D4 y agregarla a D2 (interpretar que la glucosa no subió).
  - **C.** Otra ventana (indíquela).
- **Recomendación: A.** Reconocer que la dosis no llegó ya es parte de la evidencia esperada en D4; ponerlo
  también en D2 contaría dos veces lo mismo.

### P-04 · TEP · Qué hace una trombólisis no indicada

- **Hoy:** una trombólisis sin indicación no disuelve el trombo; sólo sangra. Con el criterio revisado, la del
  shock obstructivo es indicada desde la llegada, así que esto afecta sobre todo a la submasiva
  (`pulmonary_embolism_33f`).
- **Opciones:**
  - **A.** Mantener: la lección es «daño sin beneficio».
  - **B.** La lisis disuelve igual que cuando está indicada, porque el fármaco no depende de la indicación, y
    conserva todo el sangrado. La decisión la juzga la evaluación (D3, C1), no un efecto ausente.
- **Recomendación: B.** «No funcionó» enseña algo falso. En la 33f la obstrucción mejoraría y la paciente
  sangraría del sitio quirúrgico: el balance entre riesgo y beneficio sigue a la vista.
- **Fuente:** el ensayo PEITHO (*N Engl J Med* 2014), en TEP de riesgo intermedio: menos descompensación
  hemodinámica, más sangrado mayor y más ACV hemorrágico. Citado de memoria; no pude verificarlo en la sesión.
- **Si elige B:** cambian las trayectorias de la 33f con lisis, sólo en encuentros nuevos.

### P-05 · TEP · Una segunda dosis de trombolítico

- **Hoy:** se registra como repetición, la sala dice que el simulador no le da efecto propio, y no disuelve
  ni sangra más (`pe_obstruction.give_thrombolysis`).
- **Opciones:**
  - **A.** Mantener.
  - **B.** La repetición no disuelve más, pero sí sangra: se suma el sangrado de una dosis, con la misma
    magnitud que la primera, sin inventar una nueva.
  - **C.** Disuelve y sangra como una dosis más.
- **Recomendación: B.** Repetir una dosis completa no tiene respaldo, y el riesgo de sangrado sí aumenta: que
  no pase nada enseña que repetir es inocuo.

### P-06 · TEP · La redacción «sustained hypotension» en D3, C1 y TDFC

- **Hoy:** las declaraciones dicen «sustained hypotension». El motor, en cambio, indica la lisis:
  - por un shock obstructivo atribuible al TEP, desde la llegada;
  - o por una hipotensión de 15 minutos consecutivos sin hipoperfusión.

  La noradrenalina sola no crea la indicación.
- **Opciones:**
  - **A.** Mantener la redacción.
  - **B.** Nueva redacción sólo para encuentros nuevos: «obstructive shock attributable to the PE, or
    sustained hypotension (SBP < 90 mmHg for 15 consecutive minutes)». La referencia TDFC aprobada de los
    encuentros anteriores no cambia.
- **Recomendación: B.** Hoy el texto y el motor dicen cosas distintas.

### P-07 · DF-23 fila 2 · Fotos de llegada

- **`pulmonary_edema_75f`:** la sala muestra V34, aprobada y del mismo contrato de llegada. Queda su
  revisión clínica: la llegada dice «Awake and oriented» con SpO2 84 %.
  - **A.** Mantener V34.
  - **B.** Volver a la vista neutral.
  - **Recomendación:** decídalo mirando la foto; no puedo juzgarla por usted.
- **`bradycardia_bb_54f`:** no hay foto aprobada para su contrato (somnoliento), y la sala muestra la vista
  neutral.
  - **A.** Mantener la vista neutral.
  - **B.** Generar una foto nueva: requiere presupuesto, generación con IA y dos revisiones humanas; no
    entra en este ciclo.
  - **Recomendación: A.**
- **Evidencia:** `docs/IMAGENES_DECISIONES_CLINICAS.md`.

### P-08 · Embarazo o FUM en cuatro casos (resto de TD-19)

- **Hoy:** `asthma_24f`, `anaphylaxis_29f`, `pulmonary_embolism_33f` y `pneumonia_46f` responden «No
  documentado». La prueba de embarazo se registra como pedida y sin resultado.
- **Opciones:**
  - **A.** Mantener «No documentado» en los cuatro.
  - **B.** Escribir en cada caso qué responde la paciente.
  - **C.** Escribirlo sólo en la 33f, la de mayor relevancia: angio-TC, contraste y anticonceptivo con
    estrógenos.
- **Recomendación: C.** El texto lo dicta usted; no lo invento. Lo implemento con sus pruebas, en inglés y en
  español.
- **Evidencia:** `docs/AUDITORIA_DF23_CICLO6.md` §4.

### P-09 · Fase 2, paso 2 · Quién lee las notas privadas docentes

- **Opciones:**
  - **A.** Sólo su autor.
  - **B.** Todo el cuerpo docente, nunca un residente, con autor y hora.
  - **C.** El autor y el administrador.
- **Recomendación: B.** Permite una retroalimentación coherente entre docentes. «Privada» significa que
  ningún residente la ve por ninguna ruta: páginas, copia del registro o PDF.

### P-10 · Fase 2, paso 3 · El portafolio de una cuenta inactiva

- **Opciones:**
  - **A.** Sólo el administrador lo pide y lo entrega.
  - **B.** Cualquier docente.
  - **C.** Nadie; se entrega al reactivar la cuenta.
- **Recomendación: A.** Una cuenta inactiva no inicia sesión, así que alguien con un rol claro debe
  responder por la entrega.

### P-11 · Los 10 scripts de regresión que fallan (diagnóstico C10-01)

- **Hechos:**
  - Ninguno está en `ACTIVE_REGRESSIONS` de `run_regressions.py`, que corre 56 y los 56 pasan. Ya estaban
    fuera antes del 2026-09-21, el commit más antiguo de la copia (el clon es superficial).
  - 7 (`v06030`, `v06031`, `v06032`, `v06033_trace_reasoning_display`, `v06037`, `v070`, `v071`) exigen, en
    su línea 3 a 5, un rótulo de versión antiguo en el código de `app.py` («MVP v0.6.0.31»…), y ahí se
    detienen sin probar nada más. Sin esa línea, 1 pasa y 6 fallan en otros fragmentos de código que ya no
    existen, por ejemplo `parse_fio2_percent`.
  - 2 (`v06027`, `v06029`) exigen otros textos de código antiguos.
  - 1 (`v06015_recovery`) prueba el motor antiguo (PS001): espera un llene capilar de 4 s tras la
    recuperación y hoy es de 5. Su hermano activo, `regression_v06015.py`, pasa.
- **Opciones:**
  - **A.** Dejarlos como están.
  - **B.** Declararlos retirados en `run_regressions.py`, con una lista con el motivo, más una prueba que
    exija que cada script esté activo o retirado; los archivos no se borran.
  - **C.** Borrarlos.
  - **D.** Repararlos: reescribirlos contra el código actual; no agregaría cobertura, porque duplican scripts
    activos.
- **Recomendación: B.** Desde ahora el informe diría «56/56 activos y 10 retirados», no «56 de 66».

## Revisiones con firma

| ID | Qué | Dónde | Filas |
|---|---|---|---|
| R-1 | DC9: las filas propuestas de las nueve composiciones. Las alertas señalan dónde el texto copiado habla del caso de origen, por ejemplo una glucosa de llegada que la composición no tiene | `docs/revision/DC9_COMPOSICIONES.md` | 36 (14 alertas) |
| R-2 | TD-04: el POCUS de llegada de los 14 casos C14 YES, en inglés y con su borrador en español | `docs/revision/TD04_POCUS_C14.md` | 14 |
| R-3 | Las cuatro dudas residuales de TDFC, abajo, tal como están | este documento | 4 |
| R-4 | El español de las frases del motor (C10-08) | se agrega al terminar C10-08 | — |
| R-5 | Las guías del piloto (C10-06) | se agrega al terminar C10-06 | — |

Las hojas R-1 y R-2 salen del código (`tools_review_sheets.py`) y una prueba exige que estén al día. Ninguna
aprueba nada.

**R-3 · Dudas residuales de TDFC** (`docs/tdfc/TDFC_TABLA_FINAL.md`; se mantienen hasta que usted las cambie):

- **T-1:** `anaphylaxis_29f`, C3 YES. Es la única C3 YES clara que descansa en una amenaza de vía aérea; el
  motor modela el estridor sólo como una caída de SpO₂.
- **T-2:** opioides y bradicardias tóxicas, C1 YES. Su EPA propia es C8 (no habilitada); cuentan por la
  insuficiencia respiratoria o el shock, y porque el motor obliga a revisar el plan.
- **T-3:** `hypoglycemia_76f`, C1 NO. La recurrencia podría leerse como revisión del modelo de trabajo.
- **T-4:** `acs_52m_de_winter`, F1 y C3 NO. El modelo general congestiona pasado el minuto 80; quedó fuera en
  TDFC-5.

Respuesta: `T-1 confirmo` o `T-1 cambio: …`.

## Sin decisión ahora

- **Esperan la validación externa:** «suero glucosado», KD-02·TD-35, KD-15 y TD-45, todos del lector.
- **IA posterior al encuentro:** sigue no autorizada; cada función se decide aparte, cuando usted quiera.
- **Piloto:** las condiciones A (desplegar), B (prueba de humo en el entorno desplegado) y C (su
  autorización). El runbook de C10-06 las describe.
- **Relato en español de cada caso:** se aprueba en el tablero docente de la base desplegada; no es una
  decisión de este paquete.
