# Verificación documental · R1-03, R1-04, R2-01 y MK1

Ciclo 1 del AI Advisor, puntos 5 y 6 de la aprobación docente del 2026-09-27.

**Qué se hizo:** sólo lectura. No se agregó, cambió ni retiró ningún mapping.
MK1 no se usa. Los tres desafíos no se incorporaron como UNVERIFIED ni se
retiraron.

**Límite de esta verificación:** la política de red del entorno bloquea
`www.acgme.org` y `www.royalcollege.ca`. Aquí se verificó contra lo que el
repositorio ya registra de esas fuentes, no contra los PDF.

## Estado por desafío y código

Fuentes que el repositorio registra:

- **ACGME:** *Emergency Medicine Milestones*, Worksheet 2.1, segunda revisión de
  febrero de 2021, vigente desde el 1 de julio de 2021. Está registrada como
  `acgme_em_2021` en `competency_mapping.SOURCES` (verificada el 2026-09-13) y
  descrita en `docs/CURRICULUM_PILOT.md:61`.
- **RC-PtC:** Royal College, *Pathway to Competence in the Specialty of
  Emergency Medicine*, v1.0 2018. Está descrita en `docs/CURRICULUM_PILOT.md:62`.
  **No** está en `SOURCES`.

| Desafío | Código | Fuente y página registradas | Estado |
|---|---|---|---|
| R1-03 | ACGME PC4 · PC5 · MK2 | ACGME pp. 10 · 11 · 16 | **KNOWN**: los tres están en la tabla verificada del código (`_ACGME`), al mismo estándar que los 8 desafíos de sesgo |
| R1-03 | RC ME 2.2 · ME 2.4 | RC-PtC pp. 11–14 · 15–17 | Documentado, pero a nivel de competencia CanMEDS y no de hito de EPA; fuera de `SOURCES` |
| R1-04 | ACGME PC1 · PC6 | ACGME pp. 7 · 12 | **KNOWN** (tabla `_ACGME`) |
| R1-04 | RC ME 2.4 · ME 4.1 | RC-PtC pp. 15–17 · 22–23 | Igual que en R1-03 |
| R2-01 | ACGME PC1 · PC4 · MK2 | ACGME pp. 7 · 10 · 16 | **KNOWN** (tabla `_ACGME`) |
| R2-01 | **ACGME MK1** | ACGME p. 15, «*Scientific Knowledge*» | **UNVERIFIED** respecto del estándar del código: sólo lo cita la documentación del piloto; no está en `_ACGME` ni tiene condición de evidencia |
| R2-01 | RC ME 1.6 · ME 2.4 | RC-PtC pp. 9–10 · 15–17 | Igual que en R1-03 |

## Hallazgos

1. **Corrección de la cola anterior.** DF-3 decía que «MK1» aparecía una sola vez
   en todo el repositorio (`curriculum.py:26`).
   - Esa búsqueda cubrió el código, no la documentación.
   - `docs/CURRICULUM_PILOT.md:61`, escrito con el commit inicial `8e33be5`
     (2026-09-21), cita «MK1 *Scientific Knowledge*, p. 15» de la edición que el
     docente aportó entonces.
   - **INFERRED:** la numeración de páginas es coherente con la tabla verificada
     (PC1 = p. 7 … MK2 = p. 16, con un desfase de 6 respecto de la hoja
     impresa). MK1 estaría en la hoja impresa 9.
   - **No verificado:** que el título y la página coincidan con el PDF, y el
     texto de sus niveles.
2. **El lado Royal College de los tres está a otra granularidad.**
   - Citan competencias CanMEDS *Medical Expert* del documento *Pathway to
     Competence*.
   - El pipeline de objetivos (`competency_mapping.mapping_for_challenge`) exige,
     para cada vínculo Royal College, un hito de una EPA de la *EPA Guide*: EPA,
     página e ítems de hito.
   - Para incorporarlos hay que elegir entre tres caminos, y los tres son
     decisiones metodológicas:
     - **(a)** Agregar *Pathway to Competence* como segunda fuente del Royal
       College, con vínculos a nivel de competencia y sin EPA.
     - **(b)** Anclarlos a hitos de la *EPA Guide*. Por coincidencia de código
       CanMEDS, no por similitud, los hitos ya verificados que llevan esos
       códigos son `C5.ME1.6`, `C5.ME2.2.*`, `C5.ME2.4` y `TP6.ME4.1`. Elegirlos
       sería un mapping nuevo que requiere aprobación (§9, §43.11).
     - **(c)** Entrar por ahora sólo con sus vínculos ACGME ya verificados, y el
       lado Royal College pendiente y visible como tal.
3. **Falta el contenido de diseño que el pipeline exige.**
   - `CHALLENGE_MAPPINGS` pide, por desafío:
     - conductas observables;
     - una frase de oportunidad;
     - la condición de evidencia de cada código ACGME. MK1 no la tiene.
   - Las conductas existen en español en `docs/CURRICULUM_PILOT.md:13-15`. Por
     ejemplo, para R1-03: «explicar una hipótesis causal con hallazgos; vincular
     la prioridad con esa hipótesis; anticipar cambios en perfusión además del
     ritmo; comparar la respuesta observada».
   - Pasarlas a la estructura del código es una adaptación, no una invención,
     pero requiere aprobación.
4. **Los tres están en uso (KNOWN).**
   - `curriculum.assign_challenge` asigna R1-03 y R1-04 desde primer año, y
     R2-01 desde segundo, después de exponer los desafíos de sesgo.
   - Se juegan sobre los perfiles PS001 (`encounter_generator.SUPPORTED_CHALLENGES`).
   - Cada uno de esos encuentros es hoy evidencia que no puede confirmarse
     (§9).

## Qué hace falta exactamente para verificar MK1

- **Organización:** ACGME.
- **Documento:** *Emergency Medicine Milestones*, archivo
  `emergencymedicinemilestones.pdf`, en
  <https://www.acgme.org/globalassets/pdfs/milestones/emergencymedicinemilestones.pdf>.
  Es la misma URL que `acgme_em_2021`.
- **Versión:** Worksheet 2.1; segunda revisión de febrero de 2021; vigente desde
  el 1 de julio de 2021. Hay que confirmarla en la portada.
- **Ubicación:** la subcompetencia *Medical Knowledge 1*.
  - PDF p. 15, contando la portada, según la documentación del piloto.
  - Hoja impresa 9 (INFERRED).
- **Qué hay que leer allí:**
  1. el título exacto de la subcompetencia;
  2. la página del PDF y la página impresa;
  3. el texto de los niveles 1 a 5;
  4. la versión en la portada.
- **Opcional:** el *Emergency Medicine Supplemental Guide* de ACGME, que explica
  la intención de MK1 y ayuda a juzgar si el vínculo es defendible. No es
  necesario para verificar la fuente.
- **Cómo conseguirlo, una de dos:**
  - el docente aporta esas páginas desde su copia;
  - el docente habilita `www.acgme.org` en la configuración de red del entorno.
- **Después de verificar sigue quedando una decisión metodológica:** si las
  conductas observables de R2-01 son evidencia de MK1 y con qué condición de
  evidencia, o si MK1 se retira y R2-01 queda con PC1, PC4 y MK2.

## Qué hace falta para el lado Royal College

- **Si se elige (a):**
  - *Pathway to Competence in the Specialty of Emergency Medicine*, v1.0 2018,
    vigente desde el 1 de julio de 2018, archivo
    `pathway-to-competence-emergency-medecine-e.pdf`;
  - hay que confirmar en las pp. 9–10, 11–14, 15–17 y 22–23 los códigos y el
    texto de ME 1.6, 2.2, 2.4 y 4.1;
  - el repositorio no registra su URL.
- **Si se elige (b):** las páginas de los hitos elegidos en la *EPA Guide* 2018
  (`rc_em_epa_2018`). C5 y TP6 ya están verificadas en el código.
- **En ambos casos:** `www.royalcollege.ca` está bloqueado desde este entorno.
