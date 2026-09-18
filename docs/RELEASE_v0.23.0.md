# v0.23.0 — Núcleo fisiológico compartido y perfiles generados acoplados

Destino exclusivo: `clinical-encounter-v0.13`.
Referencias: main `65336ab`, IA `d783593`, desarrollo anterior `333c6b5`.

## Motor recuperado

Se extrajeron 39 funciones fisiológicas de `app.py` a `clinical_physiology.py`.
La comparación AST con la versión anterior confirmó que sus cuerpos son idénticos.
Las funciones públicas de la aplicación ahora delegan en ese módulo; las llamadas
anidadas al motor, sus tratamientos y sus consecuencias mantienen el mismo núcleo.
Los callbacks de aleatoriedad y formato quedan aislados por contexto de ejecución.

El núcleo incluye precarga/respuesta a volumen, intolerancia y congestión pulmonar,
perfusión, contractilidad, presión/flujo, evolución neurológica, carga beta y nodal,
ritmo dinámico, soporte vasoactivo, oxígeno, NIV, intubación/ventilación, sedación,
cardioversión, diuresis y evolución natural/colapso. Los perfiles originales de
PS001/PS002 conservan sus coeficientes y comportamiento; no se alteran las ramas
publicadas main e IA.

## Integración con casos nuevos

`generated_physiology.py` conecta primitivas compartidas y parámetros declarados
por caso al ejecutor de Clinical Encounter:

- Compartimentos en mL: volumen retenido, extravascular, salida y déficit circulante.
  Se integra solamente el volumen entregado; el solicitado y pendiente no produce
  efecto anticipado. Redistribución, aclaramiento y diuresis conservan masa.
- Las respuestas a volumen leen compartimentos actuales. El beneficio puede
  disminuir mientras persiste la congestión. El diurético puede descongestionar y
  también reducir volumen circulante; el efecto no se suma otra vez como bolus fijo.
- Carga farmacológica activa con depósito y eliminación: la fórmula compartida
  reproduce la recurrencia por minuto del modelo original. Hay curvas separadas
  para saturación del beneficio nodal y coste miocárdico progresivo. Dosis repetidas
  se acumulan como carga activa, que luego disminuye, con un límite por caso.
- `exposure_pool` permite sumar agentes equivalentes sin duplicar su efecto. Las
  vidas medias y dosis de referencia pueden diferir; el efecto de cada pool debe
  tener una curva y magnitud coherentes. Beneficio y daño usan pools distintos.
- POCUS, examen, recurrencia y respuestas condicionadas pueden leer los
  compartimentos. Los estudios anteriores conservan los hallazgos de su toma.
- `terminal_rule` define condiciones fisiológicas sostenidas. Al cumplirse, el
  paciente entra en PEA irreversible, conserva actividad eléctrica, deja de tener
  mediciones dependientes del pulso y el reloj se detiene en el minuto del colapso.
  No se inventa respuesta a CPR ni desfibrilación: el motor original tampoco las
  ejecuta. Corregir el desencadenante reinicia el contador de deterioro sostenido.
- Contrato de generación v2, cobertura de ambos compartimentos, curvas de fármacos
  pertinentes y capacidad de hasta 64 reglas. Validación de parámetros, extremos y
  combinaciones antes de confirmar las órdenes. Recarga de módulos actualizada.

## Qué significa compartir el motor

El perfil original ejecuta literalmente las 39 funciones recuperadas. Los casos
nuevos ejecutan las primitivas portables y sus declaraciones fisiológicas; no se
construye una supuesta precarga/contractilidad PS001 a partir de un diagnóstico.
Esto no convierte a todos los pacientes en copias matemáticas de PS001 ni certifica
una equivalencia completa de su modelo presión–flujo con cualquier caso generado.
Los casos sin respuesta declarada siguen explicando la limitación de ejecución.

Las especificaciones ya guardadas no se reescriben y mantienen su trayectoria.
Para obtener compartimentos y curvas nuevas, generar un caso bajo v0.23.0. No se
utilizaron llamadas reales de IA para esta verificación.

## Verificación

- Comparación AST: 39 funciones originales preservadas sin cambios de lógica.
- 20 pruebas específicas: conservación de masa, entrega temporizada, redistribución,
  diuresis/depleción, recurrencia farmacocinética, dosis repetidas, pools entre
  agentes, límites, POCUS histórico, recuperación del desencadenante y estado terminal.
- La primera pasada completa produjo 1289 pruebas y 180 subpruebas aprobadas; tres
  fallos se corrigieron (expectativa de cobertura ampliada, umbral del escenario de
  prueba y enlace de compartimentos con POCUS). Pasada final de las suites afectadas:
  509 passed in 82.82s (0:01:22). La comprobación adicional de pools y validación pasó 67 pruebas.
- 50 de los 56 scripts históricos pasan tras actualizar tres referencias a la
  ubicación del núcleo. Los otros seis fallan también en la copia limpia anterior:
  `v06018_stop_label`, `v06024_learner_management_trace`, `v06034_turn_isolation`,
  `v081_carry_forward_repeat`, `v0821_lower_initial_ps001_bp` y
  `v0821_dynamic_ecg_strip`. No se presentan como una regresión nueva ni como pruebas
  aprobadas. Incluyen comprobaciones textuales/versiones y fixtures antiguos.
- Compilación y diff verificados. La publicación Git no verifica por sí sola la
  versión del proceso remoto de Streamlit.
