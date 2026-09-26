# Hipoglicemia: parámetros y decisiones clínicas pendientes

Etapas 0–2 del catálogo (autorización docente del 2026-09-25). Nada de lo que sigue quedó decidido por
mí. Cada punto dice qué hace hoy el motor —que la batería usa sólo como **referencia técnica**, nunca
como criterio aprobado—, dónde se observó y qué habría que decidir. Donde propongo algo, está marcado
como **recomendación**.

El catálogo, las doce combinaciones y los resultados de la batería están en
`docs/CATALOGO_HIPOGLICEMIA.md`; el versionado de la evaluación, en `docs/BASE_DE_EVALUACION.md`.

---

## A. Lo que la batería hizo visible

### DC1 · Estado de conciencia al llegar frente al umbral del motor

- **Qué pasa.** `hypoglycemia_28m` llega *Drowsy* con 34 mg/dL y `hypoglycemia_54m_thiamine` *Drowsy*
  con 32 mg/dL. El motor deriva la conciencia sólo de la glucosa (P3: obnubilado entre 25 y 44 mg/dL),
  así que al primer minuto muestra *Obtunded* sin que la glucosa haya cambiado. Lo mismo en las dos
  composiciones severas que heredan esos relatos.
- **Dónde.** Comprobación T12, fallida en 4 de 12 configuraciones y clasificada como *decisión clínica
  pendiente*, no como defecto técnico: corregirla exige elegir qué es lo correcto.
- **Opciones.** (a) Autorar *Obtunded* al llegar (cambia la presentación y el examen de dos casos del
  banco). (b) Mover el umbral del motor (cambia toda la familia). (c) Que el motor conserve el estado
  autorado mientras la glucosa no cambie de banda (cambia la lógica del motor).
- **Recomendación:** (c), porque conserva lo autorado y elimina el salto. Cambia el comportamiento del
  banco, así que requiere tu decisión.

### DC2 · La vía fallida no se ve antes de usarla

- **Qué pasa.** Nada en la presentación, la historia ni el examen menciona la vía con que llega. Se
  descubre sólo al dar glucosa en bolo por ella: el motor avisa («La glucosa no pasa…») y la glucosa
  apenas sube. Quien instala una vía nueva antes de la primera dosis nunca se encuentra con la falla, y
  quien empieza con glucagón endovenoso o una infusión por esa vía tampoco (DC4).
- **Recomendación:** decir al llegar que trae una vía periférica puesta por los paramédicos, sin decir
  que está fallida, para que usarla sea una decisión. La falla seguiría revelándose al usarla.

### DC3 · La vía intraósea

- **Qué pasa.** El motor trata una dosis intraósea como si pasara por la vía fallida (llega el 15 %) y
  su aviso habla del catéter del antebrazo. Además, el lector no reconoce «coloco una vía intraósea».
- **Recomendación:** que una orden intraósea cuente como un acceso nuevo. Requiere una acción del lector
  y una regla del motor, así que es una capacidad a decidir, no algo que corregí.

### DC4 · Alcance de la vía fallida: sólo la glucosa en bolo

- **Qué pasa.** La decisión 8 hizo que por la vía con que llega el paciente pase el 15 % de la glucosa en
  bolo. Su documento dejó fuera todo lo demás a propósito: «La vía perdida solo afecta a la glucosa
  endovenosa… Extenderla a todo fármaco IV es posible… no es lo que la decisión pedía»
  (`docs/DECISIONES_3_4_8_MAGNITUDES.md`). Por eso la infusión al 10 %, el glucagón, el octreótido y la
  tiamina endovenosos pasan enteros por esa vía, aunque el aviso dice que «la infusión se detiene».
- **Dónde.** Comprobación T5, fallida en las 6 configuraciones con vía fallida y clasificada como
  *decisión clínica pendiente*: por esa vía, la infusión aporta 20 mg/dL en 30 minutos frente al mismo
  paciente sin tratar, lo mismo que por una vía que funciona.
- **Consecuencias hoy.**
  - En la 54m, quien empieza con glucagón endovenoso o con una infusión por esa vía corrige la glucosa sin
    encontrarse con la falla, y la oportunidad de D4 (comprobar la entrega) queda sin objeto.
  - En las composiciones con sulfonilurea, la mantención funciona por la vía fallida.
- **El motor queda como lo dejó la decisión 8.** Llegué a extender la fracción a todo lo que pasa por la
  vía, clasificándolo como defecto técnico. Lo revertí antes de guardarlo: salía del alcance que
  decidiste y cambiaba 4 de los 20 guiones registrados de la 54m.
- **Opciones.**
  - (a) Mantenerlo.
  - (b) Aplicar la fracción a todo lo que se dé por esa vía en esta familia. La infusión, el glucagón y el
    octreótido llegarían al 15 %; el octreótido quedaría bajo su dosis mínima de 25 mcg y no actuaría; el
    aviso aparecería con lo primero que se dé.
  - (c) Aplicarla sólo a la infusión, que es lo que el aviso nombra.
- **Recomendación:** (b), porque hace coherente el aviso con lo que pasa y la falla se descubre por
  cualquier camino. Requiere tu decisión.

### DC5 · Si se amplía la vía fallida: la vía nueva y lo que ya corría

- **Sólo si en DC4 elige (b) o (c).** Al instalar una vía nueva, ¿la infusión que corría por la fallida
  pasa a llegar entera sin que nadie la reinstale, o reinstalarla debe ser una orden aparte?

---

## B. Evaluación

### DC6 · Dónde pesa la tiamina

- **Qué dice la versión 1.1.** Es una expectativa secundaria de D3: «su omisión aislada no hace inadecuada la
  corrección de la glucosa y nunca es razón para demorarla».
- **Decidir:** su peso exacto.
- **Recomendación:** tratarla como «medida complementaria» del nivel 3 de D3, de modo que su omisión sola
  no baje D3 de 2.

### DC7 · `hypo_no_thiamine`: clasificación, efecto y lo ya evaluado

- **Hasta el 2026-09-25 (cobertura 1.0):**
  - era una omisión crítica en D3, con ventana 0–60 min;
  - confirmada, restaba 3 puntos del total y contaba como evento crítico en el titular;
  - en `hypoglycemia_54m_thiamine`, bastaba con dar dextrosa sin tiamina para que el tamizaje la marcara
    como cumplida.
- **Desde la cobertura 1.1:**
  - ya no es evento crítico (corrección C-2026-09-25-05);
  - la vía fallida es una oportunidad de D4, sin evento nuevo.
- **Lo ya evaluado no cambia:**
  - los encuentros guardados antes conservan la versión 1.0, con su evento (`evaluation_basis`, estado
    *legacy*);
  - la tanda de 20 no incluye la 54m (sólo 28m y 76f), así que ninguna evaluación de la tanda se ve
    afectada.
- **Decidir:** si alguna evaluación ya confirmada de la 54m debe reevaluarse. Existe la función de
  reevaluación explícita, que pide motivo y persona y conserva la original; todavía no tiene pantalla.

### DC8 · La vía fallida como oportunidad de D4

- **Hoy.** Ventana 5–60 min. Esperado: recontrolar la glucosa tras la dosis, reconocer que no llegó y
  restituir una vía que sirva. Alternativa aceptada: instalar una vía nueva antes de la primera dosis.
- **Decidir:** la ventana, y si también debe aparecer en D2 (interpretar que la glucosa no subió).

### DC9 · Las declaraciones de las nueve composiciones

Se derivan del bloque de su mecanismo, más los bloques de vía fallida, tiamina y gravedad moderada
(`hypoglycemia_catalog.declaration_inputs`). Sus textos no han sido revisados por nadie.

---

## C. Parámetros del motor (referencia técnica)

Revisados o no, ninguno es un criterio para juzgar a un residente: la batería los usa como referencia y
avisa si cambian. Según `docs/HYPOGLYCEMIA_MAGNITUDES.md`, la mayoría son magnitudes docentes que
revisaste el 2026-09-20. Ese documento es anterior a la decisión 8, así que todavía describe la encefalopatía
de Wernicke, que ya no existe.

**Sin revisión registrada: P5 (el 30 %), P10 y P11 (sus números).**

| | Qué hace hoy | Revisión | Dónde importa |
|---|---|---|---|
| P1 | Cae 0,08 mg/dL/min con insulina o sin fármaco; 0,6 mg/dL/min con sulfonilurea hasta el octreótido | 2026-09-20 | Recurrencia, alta segura, gravedad moderada |
| P2 | Convulsión tras 20 min acumulados bajo 40 mg/dL; 10 min postictales | 2026-09-20 | Demora (R3), recuperación (R4) |
| P3 | Conciencia sólo según glucosa: ≥70 alerta, 45–69 somnoliento, 25–44 obnubilado, <25 sin respuesta | 2026-09-20 | DC1, bandas de gravedad, vía oral |
| P4 | 4 mg/dL por gramo; 10 g por minuto | 2026-09-20 | Respuesta a la ampolla (R1) |
| P5 | Glucagón: inicio 10 min, 1,6 mg/dL/min por 25 min; 2.ª dosis la mitad, 3.ª nada; sin glucógeno 30 % | Cinética: 2026-09-20. **El 30 %: sin revisión** (decisión 8) | Alternativa sin vía (R8) |
| P6 | Oral sólo alerta; inicio 5 min, 1,2 mg/dL/min por 25 min | 2026-09-20 | Error frecuente y mantención |
| P7 | Glucosado 10 %: 100 mL/h = 0,67 mg/dL/min | 2026-09-20 | Mantención con sulfonilurea (R2, R6, R9) |
| P8 | Con secreción propia, sobre 200 mg/dL: a los 30 min cae 0,8 mg/dL/min extra hasta bajar de 100 | 2026-09-20 | Sobrecorrección (R7) |
| P9 | Octreótido de 25 a 500 mcg: inicio 15 min, dura 360 min, detiene toda la caída de la sulfonilurea | 2026-09-20 | Alternativa a la infusión |
| P10 | Vía fallida: llega el 15 % de la glucosa en bolo EV/IO; lo demás pasa entero; una vía nueva la arregla | **Sin revisión**: el 15 % y el alcance (DC4) | DC2–DC5 |
| P11 | Tras un alta, glucosa <60 → vuelve a los 20 min | Principio: decisiones 1 y 2 (2026-09-21). **60 mg/dL y 20 min: sin revisión** | Alta insegura (R5) |
| P12 | La tiamina no despierta ni su ausencia deteriora | Decisión 8 (2026-09-21); sin magnitudes | T11 |

## D. Supuestos de configuración que habría que confirmar

- `hypoglycemia_76f`:
  - su glucógeno no está agotado pese a dos días de ingesta escasa;
  - su enfermedad renal crónica está en el relato y no en el motor (la recurrencia la modela sólo la
    sulfonilurea).
- `hypoglycemia_54m_thiamine`: el déficit de tiamina es un supuesto de este paciente, no una regla del
  alcohol (A3).
- Diabetes tipo 1 sin secreción propia (S1): es una simplificación; se ignora la secreción residual.
- Gravedad moderada: 52 mg/dL. Con sulfonilurea, ese paciente empeora durante el encuentro: baja de 40 a los
  20 minutos y convulsiona hacia el minuto 40 si nadie actúa.

## E. Superficie de las composiciones

Las nueve composiciones conservan el paciente y el relato de su caso de origen: el mismo hombre de 28
años, la misma mujer de 76. Para revisarlas sirve; para residentes serían reconocibles.

- **Antes de exponerlas:** decidir cómo variar la superficie (plantillas de relato y, más adelante, la IA
  fuera de la sesión del residente).
- **Condición para esa IA:** que proponga configuraciones que pasen las mismas comprobaciones y tu revisión.

## F. Nombres de la gravedad

«Severa» y «moderada» son bandas del motor. En una clasificación clínica ambas serían hipoglicemia grave:
el paciente necesita ayuda de otro.

- **Recomendación:** nombrarlas por lo que las distingue en el simulador: «bajo el umbral de convulsión» y
  «sobre el umbral de convulsión».

## G. Lo que el lector todavía no lee

Pruebas de fallas esperadas en `test_hypoglycemia_reader.py`. Cuando una empiece a funcionar, la prueba lo
avisa.

- «Coloco una vía intraósea» (DC3).
- «Reviso la vía venosa»: no es una acción ni un examen (DC2).

Una pregunta de lectura, sin prueba de falla esperada: «suero glucosado» **sin** concentración se lee como la
infusión al 10 %, la única que modela el motor. En la práctica local suele querer decir glucosado al 5 %.
**Decidir:** si se lee como 10 % o si se pregunta la concentración.

Corregido el 2026-09-26 (C-2026-09-26-03):

- «Glucosa capilar», «Glicemia capilar» y «Hemoglucotest ahora» sin verbo;
- «Nueva vía venosa», «Vía venosa nueva», «2 VVP gruesas» y «VVP» sin verbo. «Vía venosa permeable» sigue
  sin leerse como orden: describe la vía que el paciente ya tiene;
- «Bolo de…» sin verbo, de glucosa o de cristaloide, se devolvía como ilegible;
- «glucosado» como nombre del agente («Bolo de glucosado al 50% 50 mL EV» son 25 g);
- «2 ampollas de glucosado al 30%», sin volumen, se perdía sin aviso: ahora es la orden y el motor pide la
  dosis. «2 ampollas… 20 mL cada una» son 12 g (antes, 6 g); si no dice «cada una», se pregunta el total;
- «suero glucosado al 5% a 100 mL/h», «D5» o un glucosado al 20 % en infusión se leían como la infusión al
  10 %: ahora quedan como indicados, sin efecto modelado (decisión 3);
- «Consulto a endocrinología» (y nefrología, neurología, medicina interna y toxicología) preguntaba qué
  especialista.

Corregido el 2026-09-25 (C-2026-09-25-09):

- «infusión de dextrosa al 10% a 100 mL/h» se leía como un bolo de 10 g;
- «SG 10%» y «suero glucosado al 10%» no se reconocían;
- «D50 50 mL IV» y «dextrosa al 50% 50 mL EV» se perdían sin aviso.

## H. El texto de `hypoglycemia_54m_thiamine`

Corregido, por contradecir la decisión 8:

- el foco docente, que decía «sin precipitar una encefalopatía»;
- la pregunta «¿qué tratamiento hizo urgente la glucosa misma?».

Se conservan, para que los revises:

- el nistagmo y la marcha inestable al llegar: son la pista de la tiamina; el motor no los cambia;
- el hallazgo «nistagmo, que la glucosa sola no corrige».

## Lo que no hice

- No agregué capacidades clínicas.
- No cambié umbrales ni magnitudes.
- No cambié el alcance de la vía fallida (DC4).
- No expuse las composiciones a residentes.
- No registré ninguna revisión clínica.
- No hice llamadas pagadas.
