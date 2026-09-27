# Cola de decisiones del AI Advisor

Mantenida según `docs/AI_ADVISOR_CHARTER.md`, Sección 3. Contiene únicamente
recomendaciones sobre las que el docente debe decidir — no es un backlog de
ideas. Ninguna entrada de esta cola fue implementada; todas están abiertas.

Formato por entrada: PROBLEMA → EVIDENCIA → IMPACTO → RECOMENDACIÓN →
ALTERNATIVAS → COSTO/ESFUERZO → DECISIÓN REQUERIDA.

---

## DF-1 · TD1/F1/C1/C3/C4/C14 se acreditan sin oportunidad real de observación

**Categoría:** arquitectura de evidencia — prioridad alta (Charter §10).

**PROBLEMA.** `objective_is_eligible()` devuelve verdadero para estos 6 IDs en
cualquier encuentro completado, sin ninguna relación con el contenido clínico
real del caso.

**EVIDENCIA.** `competency_mapping.py:203`:
```python
return objective_id in {"TD1", "F1", "C1", "C3", "C4", "C14"}
```
Sin chequeo contra el caso — a diferencia de los Decision Challenges de sesgo
(R1-05…R3-01), que exigen `record_challenge_id(record) == objective_id`
(`competency_mapping.py:201-202`).

**IMPACTO.** Un docente podría acreditar, por ejemplo, C3 (vía aérea y
ventilación) en un encuentro sin ningún problema respiratorio relevante,
generando evidencia longitudinal que no refleja una oportunidad real
observada — exactamente el riesgo que el Charter §10 señala con el ejemplo de
airway/ventilation.

**RECOMENDACIÓN.** Extender el patrón que el sistema ya usa para los 5
dominios de la rúbrica (`case_assessment.py` + `evaluation_basis.py`): un
caso declara, por objetivo, si ofrece una oportunidad real; el código verifica
esa declaración contra el contenido efectivo del caso (un estudio declarado
tiene que estar entre las investigaciones del caso; una intervención
declarada tiene que ser una que el motor ejecute); la declaración se congela
al iniciar el encuentro (`evaluation_basis`), igual que hoy para D1-D5.

**ALTERNATIVAS.**
- **(a) Reutilizar el patrón de declaración por caso** (igual a D1-D5).
  Consistente con la arquitectura existente y auditable de la misma manera.
  Costo inicial: declarar los ~31+ casos del banco (o al menos los que estén
  en uso).
- **(b) Heurística en tiempo de evaluación**, derivando la oportunidad de
  señales ya presentes en el trace (p. ej., "¿se interpretó un POCUS?" para
  C14). Más barato, pero no distingue "no hubo oportunidad" de "hubo
  oportunidad y no se tomó" — la misma distinción que el Charter §8 exige
  preservar como NO EVALUABLE.
- **(c) Híbrido**: declarar oportunidad sólo para los casos activamente en
  uso hoy, expandiendo gradualmente.

**COSTO/ESFUERZO ESTIMADO.** (a) Alto — nuevo esquema de declaración,
verificador y declaración manual del banco. (b) Bajo — cambio acotado en
`objective_is_eligible`, pero con la debilidad señalada. (c) Medio.

**DECISIÓN REQUERIDA.** ¿(a), (b) o (c)? Si (a) o (c): ¿empezamos por los
casos ya usados en producción, o por un objetivo a la vez (p. ej. C14/POCUS
primero, por tener el criterio más verificable)?

---

## DF-2 · R1-03, R1-04, R2-01 generan encuentros pero nunca acumulan evidencia

**Categoría:** arquitectura de evidencia — Charter §7 y §9.

**PROBLEMA.** Estos tres Decision Challenges generan encuentros y declaran un
objetivo de razonamiento, pero no existen como `objective_id` en
`OBJECTIVES`: su desempeño nunca puede convertirse en observación,
confirmación ni registro longitudinal.

**EVIDENCIA.** `curriculum.py:12-27` (`_FOUNDATION_CHALLENGES`, con mapping
ACGME/RC en texto libre, sin fuente versionada); ausentes de
`objectives.py`/`OBJECTIVES`; `progress_store.py` (`_objective()`) rechaza
cualquier `objective_id` fuera de ese diccionario.

**IMPACTO.** Inconsistente con el modelo arquitectónico objetivo (Charter
§8): el encuentro crea oportunidad, pero no hay manera de que el faculty la
confirme como evidencia longitudinal para estos tres.

**RECOMENDACIÓN.** Aplicar el mismo patrón que ya usan los 8 Decision
Challenges de sesgo (`competency_mapping.objective_definitions`), una vez
resuelto DF-3 (verificación de MK1).

**ALTERNATIVAS.**
- **(a)** Verificar y estructurar sus tres mappings al mismo estándar que los
  8 (fuente, página, versión, en `SOURCES`) antes de darles entrada completa
  en `OBJECTIVES`.
- **(b)** Incorporarlos ya, con el mapping actual marcado explícitamente
  UNVERIFIED hasta completar la verificación — menor costo inmediato, pero
  introduce en el registro longitudinal objetivos con trazabilidad más débil
  que el resto.

**COSTO/ESFUERZO ESTIMADO.** (a) Medio (verificación documental + trabajo de
código simétrico al ya existente). (b) Bajo, con deuda de trazabilidad
explícita.

**DECISIÓN REQUERIDA.** ¿(a) o (b)? ¿Alguna razón para NO incorporar estos
tres al mismo pipeline (por ejemplo, si ya se consideran reemplazados por los
8 más nuevos)?

---

## DF-3 · MK1 (ACGME) de R2-01 no tiene fuente verificable en el repositorio

**Categoría:** mapping ACGME/Royal College — Charter §9, punto 2 (prioridad
explícita).

**PROBLEMA.** R2-01 cita el código ACGME "MK1", que no aparece en ninguna
tabla de fuente verificada del repositorio.

**EVIDENCIA.** `competency_mapping.py`, diccionario `_ACGME`, sólo define
`PC1`–`PC6` y `MK2` (los 7 códigos que sí usan los 8 Decision Challenges de
sesgo, cada uno con página, URL y versión verificadas contra el PDF oficial).
Un grep exhaustivo de "MK1" en todo el árbol del repositorio da un único
resultado: `curriculum.py:26`.

**INTENTO DE VERIFICACIÓN (esta sesión).** Se intentó obtener el PDF oficial
de ACGME (`https://www.acgme.org/globalassets/pdfs/milestones/
emergencymedicinemilestones.pdf`, la misma URL ya citada en `SOURCES` del
código) para confirmar el título exacto y la página de MK1. **La red de este
entorno bloquea el dominio `acgme.org`**, así que no se pudo verificar desde
aquí. No se sustituyó por una fuente no oficial ni se adivinó un número de
página.

**IMPACTO.** Si R2-01 se incorpora al registro longitudinal (DF-2) sin
resolver esto, citaría un código sin respaldo verificable — rompiendo el
estándar de trazabilidad que el resto del sistema sí cumple.

**RECOMENDACIÓN.** No usar "MK1" para R2-01 hasta verificarlo, o hasta que se
decida retirarlo.

**ALTERNATIVAS.**
- **(a)** Habilitar el acceso a `acgme.org` para este entorno (desde el menú
  del entorno en la barra de título de la sesión, en configuración de red),
  para que se pueda verificar directamente contra el PDF oficial con la misma
  convención de página ya usada (`page_convention` en `SOURCES`).
- **(b)** El docente aporta directamente la página/título de MK1 desde su
  propia copia del documento.
- **(c)** Retirar "MK1" de R2-01 y dejar sólo `PC1`/`PC4`/`MK2` (ya
  verificados) hasta tener evidencia.

**COSTO/ESFUERZO ESTIMADO.** Bajo en los tres casos — es una verificación
puntual, sin tocar código hasta tener el dato.

**DECISIÓN REQUERIDA.** ¿(a), (b) o (c)?

---

## DF-4 · C2 — la familia `trauma` no implica automáticamente oportunidad para la EPA

**Categoría:** decisión clínica/educativa — Charter §11 (recomendación
separada solicitada explícitamente).

**PROBLEMA.** C2 (Manage critical trauma resuscitation) sigue deshabilitada
(`supported: False`) desde el commit raíz del repositorio. Dos días después
de esa definición se agregó al banco una familia clínica `trauma`, hoy usada
por R2-04 y R2-05. El Charter es explícito: eso NO implica que C2 deba
habilitarse.

**EVIDENCIA.** `cognitive_catalog.py:149,171` (familia `trauma` en los
Decision Challenges R2-04/R2-05, añadida 2026-09-23, commit `2715051`);
`objectives.py` (C2 sin cambios desde `8e33be5`, 2026-09-21).

**IMPACTO.** Ninguno todavía — C2 sigue inactiva. El riesgo es a futuro, si
alguien asume que "ya hay casos de trauma" equivale a "ya hay oportunidad
para la EPA de resucitación crítica de trauma".

**RECOMENDACIÓN.** Antes de proponer cualquier cambio sobre C2, examinar el
contenido clínico real del/de los caso(s) de la familia `trauma` (sólo
lectura) para determinar si crean una oportunidad suficiente específicamente
para "manage critical trauma resuscitation" — no sólo la presencia de un
paciente traumatizado. Esto es trabajo de auditoría, no de implementación; el
resultado sería una recomendación nueva y separada, no una habilitación
directa.

**ALTERNATIVAS.** No aplica todavía — este ítem pide autorización para
auditar, no para decidir entre opciones de diseño.

**COSTO/ESFUERZO ESTIMADO.** Bajo — lectura del contenido de la familia
`trauma` en `clinical_cases`/el banco, sin tocar código.

**DECISIÓN REQUERIDA.** ¿Autoriza revisar (sólo lectura) el contenido
clínico del/de los caso(s) de trauma para informar si existe esa oportunidad,
como paso previo a cualquier recomendación sobre C2?

---

## DF-5 · C15 — sin acción, registrado para trazabilidad

**Categoría:** cerrado por el Charter, no requiere decisión.

El Charter §11 ya decide explícitamente mantener C15 deshabilitada mientras
no existan encuentros que creen oportunidad real de observar cuidados al
final de la vida/paliativos. No se encontró evidencia contraria a esa
justificación (ninguna familia clínica de ese tipo existe en el banco actual).
Sin acción pendiente; se deja registrado aquí para que la cola quede completa
frente a los 5 gaps que el Charter nombra en su §7.
