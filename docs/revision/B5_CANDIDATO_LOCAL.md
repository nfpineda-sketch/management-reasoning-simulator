# B-5 · Candidato local del piloto (2026-10-08)

> **Implementado en local, no empujado ni desplegado.** Autorización «FINAL FACULTY DECISIONS + LOCAL IMPLEMENTATION
> AUTHORIZATION» (2026-10-08). Rama `clinical-encounter-v0.13`, commits locales. No se empujó ninguna rama, no se
> creó `pilot-residents-v1` ni `phase-1-contracts-v2`, ni ningún recurso en Neon o Streamlit; no hubo despliegue
> ni GO; la Fase 1 no empezó.

## 1. Grupos de implementación

| Grupo | Contenido | Commit | Pruebas focalizadas |
|---|---|---|---|
| IG-0 | Centinela del español, exportador y verificador de aprobaciones, pruebas de integridad (sólo medición) | `a0ddd20` | ver §3 |
| IG-1 | Relato: T-1, T-2, T-3 y P-1; 30 aprobaciones (`case_text/es/approvals.json`) | `6cdc77b` | ver §3 |
| IG-2 | Rúbrica: D4 (R-1) y D5 (b); 5 aprobaciones (`rubric_text/es/approvals.json`) | `6e09682` | ver §3 |
| IG-3 | Paros y eventos: K-18, K-E5, K-E6, K-E16, TD-85 | `7cf3930` | ver §3 |
| IG-4 | Examen por estado: A-2, grupo A-6, A-9 a A-11, TD-84 | `30334bb` | ver §3 |
| IG-5 | X-1 (105/105): V-9, preguntas, compuerta, rótulos, monitor, ECG, tratamientos, cierre, J, R-4 activo, XR-18, documentos en español | `71aeb08` | ver §3 |
| IG-6 | Guías H-62 e I-63 (sin firma), Decision File, deuda, readiness, runbook, F0-11, propuesta de arquitectura | `ba94fc9` | pruebas de documentos |
| IG-7 | Registro de correcciones (C-2026-10-08-02 a -06; -01 entró con IG-5), manifiesto de congelamiento regenerado (sin diferencias: la batería y las decisiones de congelamiento no cambian), este documento | `ef1051c` | ver §3 |
| Recertificación 1 | Encabezado del intento repetido como en v0.8.1 (regresión v081); revisión adversarial H-1 a H-4 (la pregunta de la vía, las palabras del residente, las ranuras de plantilla en el centinela, ES-P2); C-2026-10-08-07; catálogo de hipoglicemia regenerado con su herramienta | `ba4e6c9` | ver §3 |

**Detenido para decisión docente:** los 12 textos de TD-86 (`docs/revision/B5_IG5_PENDIENTES_DOCENTES.md`): ES-P1 a
ES-P7, que el centinela ve en la sala, y ES-P8 a ES-P12, que la sala muestra sólo con ciertas órdenes.

## 2. Candidato

**No hay candidato final.** El HEAD de implementación es `ba4e6c98bbeb86727919b3e223cba11bd5461dfa`; el candidato
sigue moviéndose: falta aplicar la redacción docente de ES-P1 a ES-P7 (y de ES-P8 a ES-P12), y el centinela estricto
no puede pasar antes. Tras esa decisión: implementar, congelar el HEAD, y correr una sola vez sobre él la
recertificación completa (pruebas focalizadas, centinela, relato y rúbrica, lector y corpus congelados, Fase 0,
hipoglicemia, 56 regresiones, suite completa, preflight y SHA). El paquete de B-1 se prepara sobre ese SHA.

## 3. Recertificación local (en curso; nada de esto es la certificación final)

| Verificación | Sobre | Resultado |
|---|---|---|
| Suite completa, **diagnóstica** | `ef1051c` | Corrida válida (huella igual al inicio y al final): 7966 pruebas, 1 falla, 0 errores, 93 omitidas, 31 xfail. La falla: `docs/CATALOGO_HIPOGLICEMIA.md` desactualizado (documento generado; IG-5 cambió el guion `oral_while_not_alert`, ya declarado en C-2026-10-08-01, y el registro sumó C-01 a C-06); se regeneró con su herramienta en `ba4e6c9`. Los 31 xfail: 30 recorridos del centinela (ítems pendientes) y `test_known_gaps_of_the_reader` (previo) |
| 56 regresiones | `ef1051c` | Falló `regression_v081_carry_forward_repeat.py` (IG-5 había movido el encabezado inglés al catálogo); corregido en `ba4e6c9` |
| Revisión adversarial de IG-3 a IG-5 | `6f5f39a..ef1051c` | 4 defectos confirmados con sondas (H-1 a H-4), corregidos dentro del alcance aprobado (C-2026-10-08-07); un texto nuevo sin español aprobado (ES-P12) |
| Relato (IG-1) | `ba4e6c9` | 30 de 30 versiones aprobadas; `approvals.json` con 30 filas, sin faltantes ni duplicados, sin `trauma_hemothorax_41m`; en IG-0 (`a0ddd20`) eran 20 de 30 |
| Rúbrica (IG-2) | `ba4e6c9` | 5 de 5; en IG-0, 3 de 5 |
| Centinela, 30 casos | código de `ba4e6c9` | 0 líneas de inglés no intencional, 0 pasos detenidos; 156 apariciones, todas de ES-P1 a ES-P7 |
| Pruebas focalizadas | `ba4e6c9` (árbol antes del commit) | IG-0 a IG-2: 58; IG-3 e IG-4: 23; IG-5: 144; IG-7: 296; Fase 0: 968; hipoglicemia (preservación y catálogo): 17. Todas aprobadas |
| 56 regresiones | `ba4e6c9` (árbol antes del commit) | 56 de 56; 10 retiradas |
| Lector congelado y corpus | `ba4e6c9` | 0 líneas de diferencia en los cinco archivos del lector desde `009aadb`; `validation/` sin cambios |
