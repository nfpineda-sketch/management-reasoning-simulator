# Guía docente · piloto formativo

Para quien revisa encuentros durante el piloto. El detalle técnico está en `docs/RUNBOOK_PILOTO.md` y en
`docs/READINESS_PILOTO_FORMATIVO.md`.

> **Estado (R-5, 2026-09-30): borrador pendiente de su aprobación.** La firma de esta guía sigue pendiente.
> Abajo se distinguen tres cosas: lo que usted **autorizó**, lo que ya está **implementado** (sólo en
> encuentros nuevos) y lo que todavía **espera su aprobación**.

## Lo esencial

- **Cada juicio es del docente.** La IA no asigna ni propone nada durante el piloto: durante el encuentro
  está apagada, y después del encuentro no está autorizada. No hay nota global, ranking ni tabla de
  posiciones.
- **El residente ve el foco de aprendizaje después de su revisión**, no al cerrar el encuentro. Usted lo
  ve durante la revisión.
- **Casos:** los 31 del banco, asignados por desafío y año de formación. Las composiciones de hipoglicemia
  y los casos escritos por IA no se usan.

## Revisar un encuentro

1. **Abra el encuentro completado** desde el panel docente («Resident activity and recorded evidence»).
2. **Lea el registro:** qué escribió el residente, cómo se leyó cada orden, qué se ejecutó y qué pasó
   con el paciente.
3. **Puntúe la rúbrica** («Management reasoning rubric - pilot 1.0»), de 0 a 3 por dominio, o «No
   evaluable» si el encuentro no dio la oportunidad. Confírmela.
4. **Registre observaciones por objetivo**, cuando correspondan, con su evidencia, profundidad y
   autonomía. Una orden reconocida o un buen desenlace no dan crédito solos.
5. **Para corregir un registro,** anule la evaluación con un motivo («Void assessment»). El original y el
   motivo quedan en el historial.

## Elegir el próximo caso de un residente

- **Requisito:** un administrador debe autorizarlo para ese residente («Who may choose a resident's
  cases»).
- **Cómo:** en «Direct a resident's next encounter» elige el desafío y el caso, siempre con un motivo.
- **El residente no lo sabe:** ni que el caso fue elegido, ni cuál es, ni por qué.

## Decisiones del 2026-09-30

**Autorizadas por usted e implementadas** (sólo en encuentros nuevos; los anteriores conservan su registro y
la declaración con que se congelaron):

- **Trombólisis en el TEP (P-04, P-05, P-06).**
  - La lisis actúa sobre el trombo esté o no indicada, y su riesgo de sangrado es el que ya declaraba el
    caso. La sala no promete mejoría: lo que cambia se ve al reevaluar.
  - La indicación se juzga con el estado del minuto en que se dio: una mejoría posterior no la vuelve
    correcta.
  - El resto de un esquema de alteplasa completa la primera dosis. Cualquier otra dosis posterior es un
    **segundo curso**: queda registrado con su exposición adicional, y el simulador no le da reperfusión
    ni sangrado propios. Es una simplificación, no evidencia de que repetir no tenga efecto.
  - El criterio escrito en D3, en el evento crítico y en C1 es el que aplica el motor: shock obstructivo
    atribuible al TEP, reconocido desde que está presente, o hipotensión sostenida de 15 minutos. Un
    vasopresor que la presión no necesita no es ninguno de los dos.
- **`anaphylaxis_29f`, C3 (R-3).** Es una oportunidad **parcial**: confirme C3 sólo si aparece la
  anticipación de la vía aérea (nombrar la amenaza, pedir ayuda capaz de manejarla o prepararla,
  reevaluar el estridor). Nunca por la adrenalina y el oxígeno solos. La ejecución no se observa: intubar
  siempre resulta.
- **Estridor después de intubar (TD-47).** Con el tubo, la sala ya no ausculta estridor ni lo cobra en la
  saturación. La anafilaxia sigue su curso.
- **Criterios C14 de dos casos (R-2).**
  - `acs_61m_posterior`: no se exige reconocer la hipocinesia posterior sutil, que el informe entrega. Una
    aorta no dilatada en el POCUS no descarta una disección.
  - `acs_70f_left_main`: un bolo pequeño, justificado y reevaluado no se penaliza por sí solo. Se evalúa
    en su contexto y por la adaptación posterior.
- **`pulmonary_edema_75f` (P-07).** Llega con la vista neutral hasta que una imagen aprobada muestre su
  dificultad respiratoria. V34 no se borró; su aprobación clínica quedó pendiente para ese estado.
- **POCUS en español (TD-46).** Mientras el relato de un caso no esté aprobado, cada línea de su POCUS o su
  E-FAST se ve entera en inglés, nunca mezclada.
- **Terminología (R-4).** «Aumento de volumen», «dolor a la palpación» y «suero glucosado» ya se usan en
  las frases de la sala que tenían español.

**Pendientes de su aprobación:**

- las 18 frases del motor en español (`docs/revision/R4_FRASES_MOTOR.md`), que siguen sin mostrarse;
- las fichas POCUS de los 14 casos C14 YES (`docs/revision/R2_POCUS_C14.md`); en dos de ellas sólo se
  aprobó el criterio;
- una foto de la 75f que muestre su dificultad respiratoria;
- esta guía y la del residente, con su firma.

## Limitaciones conocidas

Son para el docente; **no se le dicen al residente como instrucciones**.

- **Lector de órdenes:** tiene brechas registradas (TD-45; `validation/KNOWN_DEFECTS_V3.md`).
  - Un fármaco o un examen nombrado en una lista sin verbo, que el lector no conoce, puede perderse sin
    aviso.
  - Un fluido nombrado sin verbo («IV fluids 1 L») queda retenido.
  - Si una orden no se ejecutó, el registro lo muestra: evalúe el razonamiento, no el lector.
- **«Suero glucosado» sin concentración:** sigue sin decidir.
- **Fotos:** `bradycardia_bb_54f` y `pulmonary_edema_75f` muestran la vista neutral a la llegada.
- **Relato en español:** sólo se muestra el de los casos cuya traducción usted aprobó en el tablero
  docente. El resto se ve en inglés, línea por línea entera, también en el POCUS.
- **E-FAST en la sala:** hoy muestra sólo la ventana pericárdica del informe (hallazgo pendiente TD-48,
  sin corregir). En `trauma_hemothorax_41m` el derrame pleural izquierdo no se ve en ese informe.
- **TEP:** un segundo curso de trombolítico no tiene efecto propio en el simulador (simplificación
  declarada).

## Si algo no calza

Anote el encuentro y la hora, y avise al responsable del piloto. Las decisiones clínicas abiertas están
en `docs/PAQUETE_DECISIONES_CICLO10.md`.
