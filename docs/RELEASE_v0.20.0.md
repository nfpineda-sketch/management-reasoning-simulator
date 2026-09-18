# v0.20.0 — Recuperación de funciones pendientes y dinámica por caso

Destino: `clinical-encounter-v0.13`. Referencias comparadas: main `65336ab`,
IA `d783593` y desarrollo v0.19.0 `7bd4790`.

## Cambios

- Restaurada la cancelación de órdenes pendientes desde un botón o con una
  indicación independiente (`Cancel pending orders`, `Cancelar la orden pendiente`).
  Limpia órdenes y aclaraciones sin administrar tratamientos ni avanzar el reloj;
  conserva el paciente y registra la cancelación. Se procesa antes de normalizar
  con IA. Cancelar una orden pendiente no suspende un tratamiento ya iniciado.
- Preparación de vía aérea (`Prepare for intubation`, `Preparar para intubación`)
  ejecutable como preparación de dos minutos. No intuba ni administra sedación.
- Aclaraciones de dosis/unidades/vía de anticoagulantes y unidades de sangre,
  conservando las demás órdenes del conjunto y pasando por la misma validación.
- Infusiones con `washout_min` conservan efecto residual tras suspensión. La
  titulación interpola desde el efecto alcanzado hacia el nuevo objetivo; una
  continuación idéntica no reinicia la respuesta. Repetir la suspensión no
  prolonga artificialmente el efecto residual.
- Los fármacos de dosis fija pueden declarar `recovery_min`. Su efecto puede
  desaparecer y una nueva dosis volver a actuar. El registro de administración
  conserva todas las dosis realmente indicadas/entregadas.
- `state_gain` permite modular cada respuesta con una curva de 2–8 puntos basada
  en fisiología declarada, tiempo o volumen entregado. Se pueden definir beneficio
  decreciente y daño creciente como respuestas separadas, o relacionar una respuesta
  con la frecuencia/otros parámetros influidos por otras intervenciones.

## Aplicación transversal y alcance

La generación nueva exige curvas explícitas para fluidos, retirada gradual para
norepinefrina/dobutamina/nitroglicerina, y recuperación para beta-bloqueantes,
diltiazem y amiodarona. Conserva los requisitos anteriores de oxígeno, sedación,
POCUS y ventilación. El autor define tiempos, magnitudes y curvas para ese paciente;
no se incorporan coeficientes universales del caso PS001.

Las curvas usan una instantánea común de las respuestas antes de modularlas. Este
modelo determinista evita dependencia del orden de evaluación y realimentación
circular. Es una aproximación parametrizada de las interacciones; no reconstruye
el modelo completo de precarga, volumen retenido, gasto cardíaco y resistencia
vascular del motor PS001. Factores entre cero y uno ponderan efectos previamente
autorizados; no se inventan mediciones. Fuera de los puntos de cada curva se utiliza
el factor del extremo correspondiente. La validación de límites y la ejecución
atómica permanecen activas.

Las especificaciones guardadas no se reescriben. Sin los campos nuevos, mantienen
su dinámica anterior. Para probar todos los cambios de generación, crear un caso
nuevo cuando la aplicación muestre v0.20.0.

## Verificación

- 400 pruebas de integración del intérprete, motor, generación, recarga, cobertura
  y registros docentes aprobadas.
- 21 pruebas finales específicas en `test_encounter_parity.py`, incluidas tres
  añadidas después de la pasada de integración: ejecución de heparina/sangre,
  cancelación integrada con el registro y titulación con latencia sin caída espuria.
- Siete regresiones históricas de main/IA aprobadas: cantidades de fluidos/O2,
  intérprete IA, continuidad, manejo respiratorio, sedación, reevaluación/volumen
  y razonamiento flexible.
- Compilación de módulos y comprobación del diff. Sin llamadas de generación IA
  para esta validación. La comprobación local no certifica el estado del proceso
  de Streamlit después del despliegue.
