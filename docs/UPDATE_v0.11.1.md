# Actualización local a v0.11.1

Esta actualización separa el progreso del residente de la pantalla de inicio del
encuentro. No cambia las tablas de la base de datos, las cuentas, las invitaciones,
los registros de encuentros ni las metas del programa. Usa las mismas dependencias
que v0.11.0.

## Qué verá cada usuario

- **Residente, Clinical encounters:** inicio o reanudación del encuentro y acceso
  a revisiones ya completadas. No se renderizan la tabla de objetivos ni sus
  criterios y comentarios de evaluación en esta pantalla.
- **Residente, My progress:** página separada, disponible en el menú lateral del
  panel inicial, con sus observaciones, profundidad, comentarios y estado de logro.
  No identifica el objetivo asignado al próximo encuentro.
- **Durante un encuentro:** no aparece el menú de progreso. Para consultar el
  progreso general, se puede usar **Save & return to dashboard** y luego
  **My progress**. El encuentro permanece guardado y se puede reanudar.
- **Revisión final:** el objetivo específico del encuentro continúa apareciendo
  en **Learning focus for this encounter** después de finalizar la atención.
- **Docente o administrador:** conserva la selección de desafíos del sandbox,
  el panel de progreso y las herramientas de evaluación.

## Actualizar la instalación que ya tienes en Downloads

1. Descarga `management_reasoning_simulator_v0.11.1.zip` en `~/Downloads`.
2. En la pestaña de Terminal que ejecuta Streamlit, pulsa **Control + C**.
3. Ejecuta este bloque completo en esa misma pestaña:

```bash
cd ~/Downloads
unzip -o management_reasoning_simulator_v0.11.1.zip
cp -R management_reasoning_simulator_v0.11.1/. management_reasoning_simulator_v0.11.0/
cd management_reasoning_simulator_v0.11.0
export MRS_AUTH_MODE=accounts
export MRS_ALLOW_LOCAL_SQLITE=true
export MRS_DATABASE_URL="sqlite:///$PWD/local-data/accounts.sqlite3"
.venv/bin/python -m streamlit run app.py
```

La carpeta de trabajo conserva el nombre `management_reasoning_simulator_v0.11.0`,
pero la aplicación mostrará **Curriculum pilot v0.11.1**. El ZIP contiene únicamente
código, recursos, pruebas y documentación: no incluye `.streamlit/secrets.toml`,
`local-data`, `.venv` ni bases de datos. La copia incorpora los archivos de código
actualizados y conserva esos archivos locales. No vuelvas a ejecutar la creación
del administrador ni cambies la clave de OpenAI.

Vuelve a entrar con `residente_prueba_r1`. Verifica que **Clinical encounters**
no muestra objetivos y que **My progress** presenta sus contadores. Selecciona
**Clinical encounters** para comenzar o reanudar el caso.

Para una instalación nueva, usa el procedimiento de
[configuración de cuentas v0.11.0](SETUP_v0.11.0.md), sustituyendo el nombre de la
carpeta y del ZIP por v0.11.1. Esta actualización local no migra cuentas a la nube.
