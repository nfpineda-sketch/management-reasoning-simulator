# Actualización a v0.12.0: análisis docente con IA

## En la aplicación web

1. Ingresa como docente o administrador.
2. Abre **Resident activity and recorded evidence**.
3. En **Encounter record**, selecciona un encuentro con estado **completed** y
   reflexión completada.
4. En **AI faculty assessment brief**, indica la ayuda recibida durante el
   encuentro. Si no se conoce, conserva **Not known / not documented**.
5. Pulsa **Generate AI faculty brief** y revisa el análisis.
6. Descarga **Download AI faculty brief (PDF)** cuando necesites el documento.
7. Selecciona un objetivo en **Assess observed objectives** y pulsa
   **Load AI suggestion into editable form**. Revisa y edita la decisión,
   profundidad, autonomía, contexto, evidencias y feedback.
8. Confirma tu revisión y pulsa **Record objective assessment** para guardar
   tu juicio. Generar el informe, descargarlo o cargar un borrador no otorga crédito.

La IA puede abstenerse cuando falta evidencia. Eso no equivale a una evaluación
insatisfactoria: el formulario requiere una decisión docente explícita. La
autonomía desconocida también queda pendiente. La lectura posterior de la
reflexión se distingue de lo demostrado durante el manejo.

El informe es privado para docentes y administradores. El residente mantiene su
acceso al encuentro y al feedback finalmente guardado por el docente. Un objetivo
ya evaluado no recibe una segunda observación por generar otro informe. Para
corregir una evaluación utiliza el flujo existente de anulación con motivo y
nueva evaluación, que conserva el historial.

## Configuración y persistencia

Se utiliza la clave `OPENAI_API_KEY` que ya tiene la app con IA. No hay que volver
a crear usuarios ni cambiar las credenciales de la base. Si deseas un modelo
distinto para este análisis, agrega `MRS_FACULTY_MODEL` a los Secrets privados;
si se omite, se usa `OPENAI_MODEL` (con el mismo valor predeterminado del
intérprete). El modelo elegido debe admitir Responses y salidas estructuradas.

Cada generación es una solicitud explícita y tiene un límite de espera. Si la IA
no responde o devuelve evidencia inválida, no se guarda un informe nuevo y puedes
continuar la evaluación manual. Los informes anteriores permanecen guardados.
Reabrir un informe guardado o descargar su PDF no vuelve a llamar a la IA.

La app crea de forma aditiva la tabla `mrs_faculty_briefs` usando su conexión
actual a PostgreSQL (o SQLite en desarrollo local). Cada informe conserva la
versión del encuentro, huella del contenido, modelo, fecha y autor de generación.
La auditoría de una evaluación asistida identifica el borrador utilizado. El
informe no se incorpora al payload del residente y no modifica su trace.

El destino web de esta actualización es exclusivamente la rama
`ai-integration-v0.9.0` de `nfpineda-sketch/management-reasoning-simulator`, con
`app.py` como entrada. La app de la rama `main` mantiene su versión actual.

## Actualizar una copia local existente

Descarga `management_reasoning_simulator_v0.12.0.zip` en `~/Downloads`. Si
Streamlit está ejecutándose en esa Terminal, pulsa **Control + C** una vez.
Para una instalación existente en la carpeta v0.11.0:

```bash
cd ~/Downloads/management_reasoning_simulator_v0.11.0
unzip -o ../management_reasoning_simulator_v0.12.0.zip -d ..
cp -R ../management_reasoning_simulator_v0.12.0/. .
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Si tu carpeta tiene otro nombre, ajusta únicamente la primera línea. Conserva la
configuración de conexión y autenticación que ya utilizas. El ZIP contiene código,
documentación y recursos públicos; no contiene cuentas, datos de residentes,
claves, bases locales ni entornos virtuales.
