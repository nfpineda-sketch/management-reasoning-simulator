# v0.24.0 — Clinical Encounter ejecuta el núcleo completo main/IA

Destino: `nfpineda-sketch/management-reasoning-simulator`, rama `clinical-encounter-v0.13`.
Referencias comparadas: main `65336ab`, IA `d783593`, desarrollo anterior `53a463d`.

## Brecha principal resuelta

v0.23 compartía funciones y primitivas, pero los casos generados todavía ejecutaban
trayectorias declaradas separadas. v0.24 conecta `coupled_encounter.py` al ejecutor
completo `clinical_physiology.py`: cada minuto llama `apply_natural_disease` y su
recomputación acoplada, con el mismo estado de tratamientos, farmacocinética,
precarga, contractilidad, tono, presión, flujo, aporte de oxígeno, recuperación
neurológica, congestión, dinámica del ritmo y colapso que los casos originales.

| Área | Integración en Clinical Encounter |
| --- | --- |
| Estado inicial | Contrato v3 exige 14 variables fisiológicas explícitas y actividad infecciosa; no se copia la presentación de PS001. |
| Tratamientos nativos | Transiciones originales de fluidos, O2, NIV, intubación/ventilador, vasoactivos, beta bloqueadores, diltiazem, amiodarona, furosemida, sedación IV y cardioversión. |
| Disponibilidad | Los tratamientos nativos no necesitan una regla de respuesta escrita por la IA. |
| Dosis y tiempo | Entrega real de fluidos y fármacos temporizados; conversión de infusiones según peso; un solo reloj y acumulación farmacológica. |
| Diagnósticos | Funciones compartidas de POCUS, lactato y gases; muestras históricas conservadas, con laboratorio anclado al valor inicial propio del paciente. |
| POCUS | Dinámica LV/IVC/pulmón del núcleo, manteniendo patología focal inicial y hallazgos RV/pericardio del caso. |
| Evolución | Recuperación cerebral y PEA nativas; las reglas narrativas no sustituyen ritmo, pulso ni estado mental. |
| Generación | Perfil nativo obligatorio, previsualización real a minutos 0/1/5/15 entregada al revisor independiente y especificación congelada con hash. |

## Correcciones durante la integración

- Dobutamina conserva unidades y dosis reales; `mcg/min` se convierte por peso para
  calcular el efecto, sin relabelarlo como `mcg/kg/min`. Norepinefrina usa también
  el peso explícito del paciente.
- Dosis fraccionadas pequeñas no reciben un efecto mínimo artificial de un bolus
  completo. La saturación del fluido respeta el volumen ya entregado del mismo bolus.
- Cambiar de NIV a O2 retira la NIV interna y su continuidad temporal.
- Un beta bloqueador desconocido no se sustituye implícitamente por propranolol.
- Cardioversión no informa conversión exitosa en un ritmo que ya era sinusal.
  AF conserva el modelo original; otros ritmos necesitan metadatos explícitos de
  resultado por energía/ritmo y usan la misma actualización fisiológica.
- PEA conserva el ritmo eléctrico para el ECG; el reloj se detiene al colapso.
- Los hallazgos neurológicos propuestos por una regla no se muestran como recuperación
  presente si contradicen el estado cerebral calculado por el núcleo.

## Alcance y compatibilidad

Las terapias que no existen en main/IA (por ejemplo dextrosa, naloxona,
broncodilatadores o anticoagulación) siguen requiriendo extensiones explícitas del
caso. Sus entradas cardiorrespiratorias entran antes de la recomputación central;
no sustituyen las cifras resultantes después de ella. Esto no agrega tratamientos
ni morfologías ECG ausentes en el motor original; tampoco agrega CPR/desfibrilación.

Los encuentros guardados sin perfil nativo no se convierten inventando parámetros.
Se preserva el registro y el ejecutor de producción pide generar un caso nuevo.
El ejecutor declarativo histórico permanece para compatibilidad de pruebas, pero
no es el camino de ejecución de los nuevos casos ni un fallback en producción.

La equivalencia probada es de ejecución de software para estados y secuencias
controladas. No equivale a validación clínica universal de cualquier caso que
pueda redactar una IA. No se hicieron llamadas reales de generación de IA en las
pruebas; autor y revisor se ejercitaron con respuestas controladas.

## Verificación

- Suite general: **1324 pruebas y 180 subpruebas aprobadas** (237,94 s).
- Suites de las áreas afectadas: **540 pruebas aprobadas** (84,72 s).
- Última pasada tras corregir el aislamiento entre pacientes y las unidades al
  suspender dobutamina: **74 pruebas aprobadas** (4,46 s).
- Equivalencia directa de estado oculto y observaciones para 13 intervenciones
  nativas durante cinco minutos, usando llamadas de referencia independientes
  del despachador del adaptador. Además: continuidad, dosis por peso, entrega
  temporizada, historias diagnósticas, conversión no-AF, PEA e integridad atómica.
- Regresiones históricas: **50 de 56 aprobadas**. Los seis fallos son los mismos
  documentados antes de esta versión: `v06018_stop_label`,
  `v06024_learner_management_trace`, `v06034_turn_isolation`,
  `v081_carry_forward_repeat`, `v0821_lower_initial_ps001_bp` y
  `v0821_dynamic_ecg_strip`. No se contabilizan como aprobados.
- Compilación y `git diff --check` sin errores. La publicación de la rama no
  verifica por sí sola la versión del proceso remoto de Streamlit.
