# Guía docente · piloto formativo

Para quien revisa encuentros durante el piloto. El detalle técnico está en `docs/RUNBOOK_PILOTO.md` y en
`docs/READINESS_PILOTO_FORMATIVO.md`.

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

## Limitaciones conocidas

Son para el docente; **no se le dicen al residente como instrucciones**.

- **Lector de órdenes:** tiene brechas registradas (TD-45; `validation/KNOWN_DEFECTS_V3.md`).
  - Un fármaco o un examen nombrado en una lista sin verbo, que el lector no conoce, puede perderse sin
    aviso.
  - Un fluido nombrado sin verbo («IV fluids 1 L») queda retenido.
  - Si una orden no se ejecutó, el registro lo muestra: evalúe el razonamiento, no el lector.
- **«Suero glucosado» sin concentración:** sigue sin decidir.
- **Fotos:** `bradycardia_bb_54f` muestra la vista neutral; `pulmonary_edema_75f`, la foto V34.
- **Relato en español:** sólo se muestra el de los casos cuya traducción usted aprobó en el tablero
  docente. El resto se ve en inglés.

## Si algo no calza

Anote el encuentro y la hora, y avise al responsable del piloto. Las decisiones clínicas abiertas están
en `docs/PAQUETE_DECISIONES_CICLO10.md`.
