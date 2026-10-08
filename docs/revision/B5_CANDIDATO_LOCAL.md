# B-5 · Candidato local del piloto (2026-10-08)

> **Implementado en local, no empujado ni desplegado.** Autorización «FINAL FACULTY DECISIONS + LOCAL IMPLEMENTATION
> AUTHORIZATION» (2026-10-08), y después «FACULTY DECISIONS — ES-P1 TO ES-P7» y «Faculty now resolves ES-P8 through
> ES-P13» (2026-10-08). Rama `clinical-encounter-v0.13`, commits locales. No se empujó ninguna rama, no se
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
| ES-P1 a ES-P7 | Redacción docente del 2026-10-08 (C-2026-10-08-08): ayuda del selector, «Preguntar por: {tema}», «Última respuesta», ficha clínica tras el cierre, frase de gastroenterología exacta, «unidades» y nombres de respaldo; ES-P8 a ES-P13 declarados pendientes fuera del recorrido | `1db80bb` | ver §3 |
| ES-P8 a ES-P13 y candidato final | Redacción docente del 2026-10-08 (C-2026-10-08-09): las 15 aclaraciones del lector, la dosis del ácido tranexámico sin dosis escrita, las dos fibrilaciones, la última línea de una orden retenida y la frase de gastroenterología con la presión sistólica; ES-P11 canónico; mini-pase adversarial (las palabras del residente antes de cualquier frase de la sala, sin tope de largo; «unidades/kg» y «unidades PO» por ES-P6); guías H-62 e I-63 al candidato, sin firma; documentos | el candidato final (su SHA, en el informe de la certificación) | ver §3 |

**Sin decisiones docentes de texto pendientes:** los 13 ítems de TD-86 (ES-P1 a ES-P13) están decididos e
implementados (`docs/revision/B5_IG5_PENDIENTES_DOCENTES.md`).

## 2. Candidato

**Candidato local congelado: `37c9afb1094327dd498857aa97a91820ddb4fe4c`** (árbol
`81e290c6d35773c0ddfc488194c0f691d3cf7774`). La primera certificación, sobre `2dc09e4`, halló en la suite completa
una prueba que dependía del orden y que ya fallaba igual en `189f47e` (C-2026-10-08-10); se corrigió en la prueba,
el SHA cambió y la certificación completa se repitió una sola vez sobre `37c9afb` (§3). Desde el 2026-10-08 el
candidato está congelado: no cambian el runtime, los textos de los casos, la rúbrica, las cadenas de idioma, la
conducta clínica, las aprobaciones ni las pruebas, salvo que B-1 demuestre un defecto real; los commits posteriores
son sólo de documentación. B-1 sobre este SHA: autorizado y PENDING EXTERNAL
(`docs/revision/PRE_DEPLOYMENT_READINESS_2026_10_06.md`, §21).

## 3. Recertificación local y certificación final

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
| Tras ES-P1 a ES-P7: relato y rúbrica | `1db80bb` (árbol antes del commit) | 30 de 30 y 5 de 5, sin cambios |
| Tras ES-P1 a ES-P7: centinela, 30 casos | código de `1db80bb` | 0 líneas en inglés, 0 pasos detenidos; ES-P8 a ES-P13 declarados pendientes fuera del recorrido |
| Tras ES-P1 a ES-P7: pruebas focalizadas | `1db80bb` (árbol antes del commit) | IG-0 a IG-2: 59 y 1 xfail (pendientes fuera del recorrido); IG-3 e IG-4: 23; IG-5: 151; IG-7: 298; hipoglicemia: 17; pantallas y textos: 416; Fase 0: 968 |
| Tras ES-P1 a ES-P7: 56 regresiones, lector y corpus | `1db80bb` (árbol antes del commit) | 56 de 56; lector congelado y `validation/` sin cambios |
| Tras ES-P8 a ES-P13: centinela estricto, 30 casos | árbol antes del mini-pase (sobre `189f47e`) | 30 de 30; 0 líneas en inglés; 0 pasos detenidos; 0 pendientes dentro o fuera del recorrido; salida 0 en las tres tandas |
| Mini-pase adversarial de la capa de idioma | árbol sobre `189f47e` | 4 hallazgos corregidos dentro del alcance aprobado, con prueba: 3 bloqueantes (una frase de la sala escrita por el residente se traducía dentro de su lista o su cita; tope de 500 caracteres para lo que escribió; «units/kg» en la dosis por kilo) y 1 menor («units PO»). 5 informativos sin cambio: «1 units» ya está así en inglés; el detector marcaría la lista del residente en ES-P12 si un recorrido llegara a ella; un ítem que termina en punto deja «..»; PAS no entera y más de 256 citas, inalcanzables |
| Tras el mini-pase: pruebas que tocan el idioma (39 archivos) | árbol antes del commit | 1681 aprobadas, 0 fallidas |
| Tras el mini-pase: 56 regresiones | árbol antes del commit | 56 de 56; 10 retiradas |
| Primera certificación | `2dc09e4` | Pruebas focalizadas 1981, centinela 30/30 limpio, relato 30/30, rúbrica 5/5, lector y corpus congelados, 56/56 regresiones y preflight LISTA; la suite completa: 8023 pruebas, **1 falla** (dependía del orden; ya fallaba en `189f47e`; C-2026-10-08-10). Invalidada: el SHA cambió |
| **Certificación final única: SHA y árbol** | `37c9afb` | SHA exacto; árbol limpio (0 cambios) |
| Certificación final: relato y rúbrica | `37c9afb` | 30 de 30 y 5 de 5 (`--check` y `--verify`, también `--rubric`): coinciden y se activan |
| Certificación final: lector y corpus | `37c9afb` | 0 líneas de diferencia en los cinco archivos del lector desde `009aadb`; `validation/` sin cambios |
| Certificación final: centinela estricto | `37c9afb` | 30 de 30 casos en 3 tandas; 0 líneas en inglés; 0 pasos detenidos; 0 pendientes dentro o fuera del recorrido; salida 0 |
| Certificación final: pruebas focalizadas (40 archivos) | `37c9afb` | 1983 aprobadas, 0 fallidas |
| Certificación final: 56 regresiones | `37c9afb` | 56 de 56; 10 retiradas |
| Certificación final: suite completa | `37c9afb` | 8025 pruebas, 0 fallas, 0 errores, 93 omitidas, 1 xfail; huella igual al inicio y al final (válida) |
| Certificación final: Fase 0 (de la suite) | `37c9afb` | 968 aprobadas; las 10 de PostgreSQL, omitidas sin URL |
| Certificación final: hipoglicemia (de la suite) | `37c9afb` | 123 aprobadas (preservación 6, catálogo 28) y 1 xfail declarado (brecha conocida del lector) |
| Certificación final: preflight local | `37c9afb` | «Configuración del piloto: LISTA», salida 0, sin `--connect` |
| Paquete de B-1 | `37c9afb` | bundle y ayudantes con sus sumas verificadas; B-1 no ejecutado: PENDING EXTERNAL |

