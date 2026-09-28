# Arquitectura: lo implementado y lo planificado

Ciclo 5 del AI Advisor (59BO), 2026-09-28.

**Dos diagramas separados a propósito:**

- **el primero es el código de `ec1c77f`** (la corrección nocturna 59Z no
  cambia la arquitectura);
- **el segundo es la dirección acordada, NO implementada.**

Una documentación futura no debería mezclarlos.

Los conceptos están en `DATA_DICTIONARY.md` y las fuentes de verdad en
`SOURCE_OF_TRUTH_MAP.md`.

## 1. IMPLEMENTADO (arquitectura real actual)

```mermaid
flowchart TD
    subgraph Residente["Residente (Streamlit, app.py)"]
        R1[Inicia un Decision Challenge] --> R2[curriculum_runtime: caso del banco o generado]
        R2 --> R3[evaluation_basis.freeze: declaración + oportunidades + huella]
        R3 --> R4[(mrs_attempts.encounter_json)]
        R5[Texto libre: orden + razonamiento] --> R6[family_parser: lector determinista]
        R6 --> R7[family_engine: ejecución y fisiología]
        R5 --> R8[extract_explicit_reasoning: modelo, prioridad, expectativa]
        R7 --> R9[(payload_json.session.management_trace)]
        R8 --> R9
        R9 --> R10[Cierre y reflexión: review_completed]
    end

    subgraph IA["IA (opcional, fuera del lector y del motor)"]
        A1[Generación de casos]
        A2[Imágenes: banco con presupuesto]
        A3[Conversación con el paciente: ruta local primero]
        A4[Brief docente]
        A5[Propuesta de rúbrica]
        A6[Síntesis del Trace]
        A7[Traducción de prosa]
    end

    subgraph Docente["Docente (faculty_portal, rubric_portal, progress_portal)"]
        F1[Lee el Trace y la evidencia: objectives.evidence_items] --> F2{Oportunidad por objetivo: observation_opportunities.resolve}
        F2 -->|yes / transición| F3[progress_store.assess]
        F2 -->|no| F4[No evaluable: se rechaza]
        F3 --> F5[(mrs_progress_observations + provenance_json)]
        F6[Rúbrica D1–D5] --> F7[(mrs_rubric_reviews: confirmada)]
        F8[Confirmar objetivo] --> F9[(mrs_progress_confirmations)]
    end

    R10 --> F1
    A4 -.propone.-> F1
    A5 -.propone.-> F6
    F5 --> P1[get_progress: Objective Progress calculado]
    F7 --> P2[rubric_progress: perfil y radar]
    F5 --> P3[competency_mapping: contribuciones DIRECT/PARTIAL]

    subgraph Validacion["Validation corpus (CLI, fuera de la app)"]
        V1[DOCX devueltos] --> V2[split] --> V3[ingest] --> V4[run: página real] --> V5[adjudicate] --> V6[report + baseline]
    end
```

**Lo esencial:**

- **El lector y el motor son deterministas.** La IA propone; nunca registra
  evidencia.
- **Todo lo que un encuentro fue queda congelado** en `mrs_attempts`.
- **Lo que el docente decide vive en sus tablas.**
- **Progreso y perfil se recalculan al leer.**

## 2. PLANIFICADO (dirección acordada; NO implementado)

```mermaid
flowchart TD
    C1[Caso] --> C2[Oportunidades revisadas explícitamente para cada objetivo]
    C2 --> C3[Sólo las oportunidades reales son evaluables: sin regla de transición]
    C3 --> O1[Observación confirmada por el docente]
    O1 --> O2[Registro de oportunidad ofrecida pero no ocurrida: DF-17, faculty override]
    O1 --> L1[Vista de linaje: meta del marco → componente → contribución → observación → encuentro → decisión del Trace]
    L1 --> X1[Exportación por marco: ACGME o Royal College]
    V[Piloto de validación: desarrollo → sealed con versión candidata congelada] --> M[Métricas de fidelidad publicables]
```

| Pieza planificada | Estado | Dónde está la decisión |
|---|---|---|
| Oportunidades revisadas para TD1, F1, C1, C3, C4 | **borrador** (ciclo 5, no escrito en el banco): 73 YES, 60 NO, 22 dudosas | DF-21 y `docs/tdfc/` |
| Retiro de la regla de transición | C14: 30 de 31 casos; los demás objetivos pendientes | DF-12 |
| *Faculty override* | **diferido** | DF-17 |
| Vista de linaje de evidencia | diseño; los datos actuales lo permiten en parte | `AUDITORIA_NOCTURNA_CICLO5.md`, anexo 59BF |
| Exportación por marco | no iniciada | `AUDITORIA_NOCTURNA_CICLO5.md`, anexo 59BG |
| Piloto de validación ejecutado | **listo, no enviado** | DF-15 |
