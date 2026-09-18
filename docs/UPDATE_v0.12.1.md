# v0.12.1: informe docente breve y acceso al encuentro

El PDF predeterminado reúne en dos páginas las seis propuestas por objetivo,
evidencias seleccionadas, prioridades de revisión y preguntas para el debriefing.
El análisis completo se conserva en pantalla y como PDF adicional. Las propuestas
y las evaluaciones ya guardadas no se modifican al cambiar la presentación.

## Flujo docente

1. Abre **Resident activity and recorded evidence** y elige el encuentro completado.
   El selector muestra residente, desafío, estado y fecha.
2. En **AI faculty assessment brief**, descarga **Download 2-page faculty brief (PDF)**.
   Los informes guardados anteriormente también usan este formato sin otra llamada a IA.
3. Comprueba las propuestas y los puntos de revisión. En el PDF, **Open this encounter**
   abre el encuentro en la app, después de iniciar sesión con una cuenta autorizada.
4. En **Assess observed objectives**, selecciona un objetivo y, si resulta útil,
   pulsa **Load AI suggestion into editable form**. Revisa los campos, resuelve lo
   que falte y registra tu juicio con **Record objective assessment**.
5. Para consultar el detalle, abre **Read the analysis and debriefing questions**
   y **Download full faculty analysis (PDF)**. El registro fuente sigue disponible
   en **Read the recorded evidence** y **Complete encounter record and export**.

Los extractos del resumen se identifican como selecciones. Ninguna descarga,
enlace o borrador guarda una evaluación, concede crédito o establece autonomía.
La ayuda desconocida continúa pendiente del juicio docente. El prompt 1.1 limita
la repetición en nuevas generaciones y conserva las advertencias pertinentes;
los informes anteriores del prompt 1.0 continúan siendo válidos.

## Despliegue y enlace del PDF

La actualización corresponde a la rama **ai-integration-v0.9.0**. Tras actualizar
los archivos en Streamlit Cloud, usa **Manage app → Reboot app** para recargar
también los módulos importados. La rama `main` no forma parte de esta actualización.

El enlace predeterminado del informe apunta a
`https://clinical-management-reasoning-ai.streamlit.app/`. Para desplegar esta
copia en otra dirección, define `MRS_PUBLIC_APP_URL` con una URL HTTPS pública,
sin credenciales, parámetros ni fragmentos. El enlace solo añade `faculty_attempt`;
no contiene tokens y no sustituye la autenticación ni los permisos existentes.

## Copia local

Descarga `management_reasoning_simulator_v0.12.1.zip` en `~/Downloads`. Si tu
instalación existente está en la carpeta v0.11.0, detén Streamlit con **Control+C**
y ejecuta:

```bash
cd ~/Downloads/management_reasoning_simulator_v0.11.0
unzip -o ../management_reasoning_simulator_v0.12.1.zip -d ..
cp -R ../management_reasoning_simulator_v0.12.1/. .
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Si tu carpeta tiene otro nombre, cambia solo la primera línea. Conserva tu
configuración de autenticación y conexión existente. El ZIP incluye código,
documentación y recursos públicos; excluye datos de residentes y credenciales.
