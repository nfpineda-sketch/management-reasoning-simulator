# Auditoría C2 · ¿crean los casos trauma una oportunidad para observar «Manage critical trauma resuscitation»?

Ciclo 1 del AI Advisor, quick win QW2, aprobado por el docente el 2026-09-27.

- **Tipo:** sólo lectura. No se habilitó C2 ni se cambió ninguna regla, texto u
  objetivo.
- **Código revisado:** commit `3719b0c`.
- **Charter:** §11 pide determinar si estos encuentros crean oportunidades
  suficientes para observar *management of critical trauma resuscitation*, «y no
  simplemente la presencia de un paciente traumatizado».

## Respuesta corta

- **Para el componente simulado de manejo, sí (INFERRED, con evidencia fuerte
  del código).**
  - Los dos casos no son «un paciente traumatizado» con otro tema de fondo.
  - Están construidos alrededor de decisiones de resucitación de trauma: la x de
    xABCDE, el control de hemorragia, la reposición con sangre y no sólo con
    cristaloide, el drenaje torácico, la búsqueda de otra fuente y la necesidad
    de pabellón.
  - Tienen reloj de sangrado, acciones ejecutables, oportunidades D1–D5
    declaradas y verificadas, y eventos críticos propios de trauma.
- **Para la amplitud de lo que C2 nombra, todavía no (KNOWN).** Hay 2 casos, 2
  mecanismos aislados, una fuente de sangrado por caso, adultos, sin equipo y
  sin quirófano. Una EPA de resucitación de trauma crítico abarca más que eso.
- **Recomendación:** mantener C2 deshabilitada, como ya decide el charter. Si se
  habilita, que sea sólo a través del mecanismo general de oportunidades
  (`docs/PROPUESTA_OBSERVATION_OPPORTUNITIES.md`), caso por caso y con un alcance
  explícitamente acotado. Es una decisión clínica (DF-4 en la cola).

## Evidencia por caso (KNOWN, desde el código)

| | `trauma_limb_hemorrhage_27m` | `trauma_hemothorax_41m` |
|---|---|---|
| Mecanismo | Herida penetrante de muslo por maquinaria | Colisión de alta energía, conductor con cinturón |
| Llegada | PA 96/54, FC 132, llene 4 s, lactato 4,4, Hb 10,2 | PA 88/50, FC 126, FR 28, PaO₂ 66, lactato 4,8, Hb 9,4 |
| Problema central | Hemorragia externa exsanguinante: controlarla antes que todo lo demás | Hemotórax masivo: drenar y reanimar a la vez; si sigue inestable, buscar otra fuente y luego pabellón |
| Lo que el motor modela | Sangrado por minuto por fuente abierta (`trauma_hemorrhage.py`); déficit de volumen, shock y paro al 50 %; sangre frente a cristaloide; ácido tranexámico | Lo mismo, más la colección torácica que sigue llenándose tras el drenaje |
| Acciones ejecutables relevantes | Torniquete, presión directa, packing, sangre, ácido tranexámico, fluidos, consulta, destino | Tubo pleural o aguja, sangre, ácido tranexámico, E-FAST o radiografía de pelvis repetidos, consulta, destino |
| Estudios propios | E-FAST (5 ventanas), radiografía de pelvis, radiografía de tórax, POCUS | Los mismos |
| Declaración D1–D5 | Las 5 declaradas, verificadas contra el caso (`case_assessment.verify`) | Las 5 declaradas y verificadas |
| Eventos críticos | `trauma_no_hemorrhage_control`, `trauma_crystalloid_instead_of_blood` | `trauma_undrained_hemothorax`, `trauma_drained_and_never_looked_again` |
| Límites declarados | Sin quirófano (se registra la derivación, nunca su resultado); sin toracotomía de reanimación ni REBOA | Los mismos |

Las decisiones docentes del 2026-09-23 están recogidas en el código:

- la x de xABCDE, el hemotórax definido por la inestabilidad y no por el volumen,
  y un mecanismo a la vez;
- sus pruebas de motor están en `test_the_families_added_2026_09_23.py`.

## Lo que estos encuentros no ofrecen (KNOWN salvo indicación)

- **Variedad de mecanismo y fuente.** Hay 2 casos con una fuente cada uno, de
  tipo externa y torácica.
  - El motor también modela fuentes pélvica y abdominal, y la faja pélvica es
    ejecutable, pero ningún caso las usa.
  - No hay trauma multisistémico, TCE, vía aérea comprometida por trauma,
    quemados, ni trauma pediátrico, geriátrico u obstétrico.
- **Coordinación del equipo y liderazgo.** No se simulan. Es la misma limitación
  que ya declara C1.
- **Tratamiento definitivo.** No hay quirófano: el encuentro evalúa reconocer
  que hace falta y sostener al paciente hasta llegar a él.
- **Activación de transfusión masiva como orden.** El lector no tiene una
  expresión para «protocolo de transfusión masiva»; existe la orden de sangre
  por unidades.
- **Lectura EN/ES de órdenes de trauma sin medir.** El corpus de ensayo no
  incluye la familia trauma (`docs/MEDICION_RECONOCIMIENTO_ORDENES.md`).

## Exposición real a estos casos

- **Por qué desafíos entra un residente.** Sólo por dos desafíos de segundo año,
  además de la dirección de caso de un docente (`encounter_directives`):
  - R2-04: sorteo uniforme entre 14 variantes; 2 son trauma, es decir 1 de cada
    7.
  - R2-05: sorteo entre 8 variantes; 2 son trauma, es decir 1 de cada 4.
- **Quién elige el caso (KNOWN).** Un residente inicia un caso del banco con
  sorteo uniforme sembrado y sin que un modelo elija:
  - la ruta es `offline_cases.launch_options` → `_authored()`, con `api_key=""`,
    y luego `cognitive_generator.py`;
  - la generación libre por IA queda reservada al administrador desde el
    2026-09-25 (`MRS_FREE_GENERATION`);
  - si se abriera a todos, esos encuentros serían casos generados sin
    oportunidades ni eventos declarados (`evaluation_basis`, estado
    `generated`).
- **Riesgo de memorización (METHODOLOGICAL REVIEW).** La cuenta de la EPA C2 es
  de 25 observaciones (`objectives.py`, `TARGET_SOURCE`). Con 2 casos, acumular
  observaciones repitiendo los mismos dos encuentros mezcla evidencia nueva con
  memoria del caso (§27).

## Inconsistencia encontrada (no corregida)

El texto de C2 en `objectives.py` dice:

- `scope`: «Reserved for future trauma-specific simulated management
  encounters»;
- `limitation`: «Critical trauma encounters are not implemented in the current
  curriculum pilot».

Desde el 2026-09-23 esto ya no es exacto: sí existen dos encuentros de trauma. La
conclusión de mantener C2 deshabilitada sigue siendo válida, pero por otra razón
(amplitud insuficiente y oportunidad no declarada caso por caso). Cambiar ese
texto modifica la definición de un objetivo, así que queda para aprobación.

## Qué haría falta para decidir con la fuente oficial

- **Estado (UNVERIFIED).** El criterio del Royal College para C2 (rasgos clave,
  variedad de presentaciones exigida y plan de evaluación) no se pudo leer:
  la política de red del entorno bloquea `www.royalcollege.ca`.
- **Fuente:** *Royal College of Physicians and Surgeons of Canada, Emergency
  Medicine EPA Guide*, 2018.
- **Página:** C2 aparece en la p. 19 de la edición de 51 páginas (VERSION 1.0),
  según `objectives.py`.
- **Qué aporta:** con esa página se puede contrastar qué variedad de trauma exige
  la EPA con lo que el banco ofrece. Esta auditoría no inventa ese criterio.
