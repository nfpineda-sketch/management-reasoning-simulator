# v0.12.2: cancelar una orden pendiente y recuperar el intento

Corrección puntual preparada sobre la versión publicada de
`ai-integration-v0.9.0` (base `a2c706a`). Este paquete no incluye los cambios
visuales de la rama de desarrollo.

## Qué corrige

- Mencionar o reevaluar **oxygen saturation** no indica administrar oxígeno.
  Las órdenes explícitas conservan su dispositivo, flujo y controles existentes.
- El texto de una expectativa negativa conserva su negación.
- **Cancel held order** permite descartar una orden aún no ejecutada. Conserva
  el mismo intento, el estado del paciente, las decisiones previas y el plan
  del intento anterior; registra la cancelación sin simular tratamiento.
- El formulario guiado acepta **0 minutos** y conserva una reevaluación
  inmediata ya solicitada, sin sustituirla por cinco minutos.

No cambia el esquema de persistencia ni exige migrar cuentas o intentos.
La actualización del código por sí sola no borra una orden pendiente ya guardada:
el usuario la cancela explícitamente con el nuevo botón.

## Retomar el Attempt 2 después de publicar la corrección

1. Abre la aplicación IA e inicia sesión con la misma cuenta.
2. Elige **Resume encounter**, si estás en el dashboard.
3. Junto a **Held order: oxygen**, pulsa **Cancel held order**.
4. Para probar la reevaluación, ingresa:

   ```text
   Reassess blood pressure, heart rate and rhythm, capillary refill, mental status, SpO2, and work of breathing now.
   ```

5. Pulsa **Submit**. Después puedes seguir manejando el caso o abrir
   **Complete Encounter & Begin Review** para probar el cierre.
6. Completa Decision Review, Expert Comparison y Adaptation Plan. El intento
   solo se registra como `completed` cuando todos los campos requeridos están
   completos. Usa **Save & return to dashboard** para regresar al inicio.

**End this attempt without completing review** conserva su comportamiento:
marca el intento incompleto como abandonado. **Next Encounter with This
Adaptation Plan** inicia otro encuentro.

## Probar una copia local

Descarga el ZIP en `~/Downloads` y ejecuta:

```bash
cd ~/Downloads
unzip management_reasoning_simulator_v0.12.2.zip
cd management_reasoning_simulator_v0.12.2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

La copia local necesita la configuración de autenticación correspondiente.
Los comandos no conectan automáticamente con los intentos de la app publicada.
Para recuperar el intento de esa app hay que publicar esta corrección en su
rama y usar la misma cuenta y configuración existentes. El paquete contiene
código y recursos públicos; no contiene credenciales ni datos de residentes.
