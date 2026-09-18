# v0.21.0 — Observaciones, oxígeno y gasometría

Destino: clinical-encounter-v0.13. Referencia recuperada: rama IA
ai-integration-v0.9.0, commit d7835936de393e1b1e46c2dea656acb1f6390535.

## Correcciones

- Monitorizar o reevaluar saturación no inicia, ajusta ni continúa oxígeno.
  Las listas de signos vitales conservan el intervalo solicitado. Un estudio
  nombrado junto con los signos vitales conserva su solicitud independiente.
- Una orden de O2 seguida de monitorización se ejecuta sin una falsa aclaración
  sobre un segundo dispositivo. Un objetivo de saturación aislado no inventa
  dispositivo ni flujo.
- Se recuperaron de IA las protecciones de `_oxygen_order_clauses`, la captura
  de expectativas explícitas positivas/negativas y el filtrado de expectativas
  inmediatas. Se conserva literalmente la negación del residente.
- Las gasometrías generadas guardan la FiO2 del soporte al obtener la muestra.
  Una ABG con PaO2 registrada deriva el cociente P/F usando esa FiO2; una VBG
  no se presenta con cociente arterial. Un cambio de soporte mientras se espera
  el resultado no modifica la muestra ni los resultados históricos. No se
  inventa PaO2 a partir de SpO2. Con dispositivos de oxígeno convencional se
  utiliza la estimación de FiO2 que ya contiene el simulador.
- Se recuperó `test_oxygen_measurements.py` de IA y se añadieron escenarios del
  motor generado. `test_pending_order_recovery.py` recupera el escenario de
  guardar/reabrir/cancelar una orden pendiente, adaptado al botón vigente.
  `test_gas_support_snapshot.py` verifica muestras antes/después de cambios de
  FiO2 y el comportamiento de VBG.

## Validación y alcance

Pasada de integración: 464 pruebas y 14 subpruebas aprobadas; siete regresiones
históricas aprobadas. La comprobación posterior del parser y observaciones incluye
la prueba adicional de signos vitales junto con lactato. Compilación y diff
verificados. No se utilizaron llamadas reales de generación IA en las pruebas.

La entrega corrige los problemas prioritarios de interacción y gasometría.
El balance completo de volumen retenido/extravascular y el deterioro terminal
siguen fuera de este cambio. Los resultados ya obtenidos conservan sus valores;
las nuevas muestras usan el soporte actual. No es necesario regenerar un caso
para corregir la interpretación de observaciones o las nuevas tomas de gasometría.
La publicación del código no constituye una comprobación del proceso de Streamlit.
