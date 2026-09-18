# Actualización a v0.11.2

Esta versión corrige la integridad de las órdenes de oxígeno y la coherencia de
la revisión posterior al encuentro. Incluye la navegación de v0.11.1:
**Clinical encounters** y **My progress** están separados para el residente.

## Correcciones

- La interpretación debe conservar una orden explícita de oxígeno, su dispositivo
  y su flujo. Si la normalización con IA no conserva esos datos, se utiliza la
  interpretación local de la entrada original.
- Una mención negada o condicional del oxígeno no constituye una orden de inicio.
  El flujo de oxígeno se distingue del volumen de una orden de fluidos cercana.
- La revisión respeta las expectativas negadas y los efectos diferidos. Una
  respuesta inmediata de presión arterial no permite juzgar la eficacia de un
  antibiótico.
- La comparación docente considera la presión y el soporte registrado en el
  momento de la decisión. Con presión suficiente, promueve reevaluar la perfusión
  y la necesidad de soporte, sin recomendar automáticamente aumentar noradrenalina.

No se cambian las tablas de cuentas ni las dependencias. Los encuentros y las
evaluaciones guardados no se eliminan. Las preguntas de revisiones ya cerradas
conservan el texto guardado; las nuevas preguntas utilizan la corrección.

## Actualizar tu copia de Downloads

Descarga `management_reasoning_simulator_v0.11.2.zip` en `~/Downloads`.
En la pestaña de Terminal que ejecuta Streamlit, pulsa **Control + C**.
Luego ejecuta:

```bash
cd ~/Downloads/management_reasoning_simulator_v0.11.0
unzip -o ../management_reasoning_simulator_v0.11.2.zip -d ..
cp -R ../management_reasoning_simulator_v0.11.2/. .
export MRS_AUTH_MODE=accounts
export MRS_ALLOW_LOCAL_SQLITE=true
export MRS_DATABASE_URL="sqlite:///$PWD/local-data/accounts.sqlite3"
.venv/bin/python -m streamlit run app.py
```

La carpeta conserva el nombre v0.11.0 y la aplicación mostrará **Curriculum pilot
v0.11.2**. El ZIP no incluye cuentas, bases de datos, contraseñas, claves de API ni
el entorno virtual: la copia incorpora el código y conserva esos archivos locales.
No vuelvas a crear el administrador ni reemplaces tus Secrets.

## Aplicación con IA en Streamlit Cloud

Destino: `nfpineda-sketch/management-reasoning-simulator`, rama
`ai-integration-v0.9.0`, archivo `app.py`.

La aplicación existente utiliza la contraseña compartida. Publicar este código
mantiene el modo de acceso configurado. Para habilitar cuentas individuales y
progreso persistente en la web, configura PostgreSQL y los ajustes descritos en
[Activación de cuentas](SETUP_v0.11.0.md#streamlit-cloud).

Los usuarios y el progreso de la base SQLite de tu Mac no se transfieren con el
código. Este paquete no realiza esa migración ni activa una base de datos remota.

Streamlit actualiza el código desde la rama vinculada; consulta la
[documentación oficial de despliegue](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).
Las credenciales se gestionan en los
[Secrets de la aplicación](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).
