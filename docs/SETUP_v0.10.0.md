# Activación de cuentas y piloto curricular v0.10.0

Esta versión se desarrolla en `ai-integration-v0.9.0`. La rama `main` no necesita cambios. La modalidad actual con `APP_PASSWORD` continúa siendo la predeterminada: publicar este código no activa cuentas ni borra esa configuración.

## Qué queda disponible al activar cuentas

- Residente: registro con invitación, contraseña propia, año asignado por administrador, encuentro asignado internamente, recuperación del caso y revisión final.
- Docente (`faculty`): elección libre entre los tres desafíos implementados, pruebas excluidas del progreso de residentes y acceso a sus registros para revisión formativa.
- Administrador (`admin`): las funciones docentes más invitaciones y modificación de roles, año y acceso.
- Guardado de especificación del encuentro, semilla, evolución, órdenes, Management Trace y reflexión. Los registros pertenecen al usuario; las revisiones finalizadas se muestran en modo de solo lectura.

El despliegue representa **un solo programa docente**. Todos los docentes y administradores pueden leer los intentos de sus residentes. No se ha implementado separación entre instituciones. Los residentes solo pueden acceder a sus propios registros. El objetivo específico aparece en el debriefing. No hay calificación automática de competencia.

## Streamlit Cloud

1. Provisionar una base **PostgreSQL persistente** y obtener su URL de conexión. Usar la conexión cifrada indicada por el proveedor, por ejemplo con `sslmode=require`. La cuenta de base de datos debe poder crear y usar las tablas `mrs_*` dentro de su esquema. No publicar esa URL en GitHub. Configurar las copias de seguridad con el proveedor.
2. En una copia local de esta versión, instalar las dependencias y ejecutar:

   ```bash
   python setup_accounts.py --print-bootstrap
   ```

   El programa pide tu nombre de usuario y una nueva contraseña de al menos 12 caracteres sin mostrarla. Genera dos líneas con el usuario y un hash con sal aleatoria. Copiar esas líneas únicamente al panel privado de Secrets de la aplicación IA. No usar la clave común como contraseña administradora.
3. En **App settings → Secrets** de la app IA, conservar las entradas actuales de OpenAI y añadir:

   ```toml
   MRS_AUTH_MODE = "accounts"
   MRS_DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
   MRS_ADMIN_USERNAME = "TU_USUARIO_GENERADO"
   MRS_ADMIN_PASSWORD_HASH = "EL_HASH_GENERADO_POR_EL_COMANDO"
   ```

   Los valores anteriores son marcadores, no credenciales. `MRS_ALLOW_LOCAL_SQLITE` debe estar ausente o ser `false` en la nube. Si la configuración de cuentas está incompleta, la aplicación cierra el acceso en lugar de volver a una modalidad abierta.
4. Guardar los Secrets y abrir la app IA. Ingresar con la contraseña que elegiste. Comprobar el acceso y crear una invitación de prueba con rol `resident` y año 1. Abrir otra ventana, crear esa cuenta y verificar que recibe un caso sin selector de desafíos.
5. Una vez creado el administrador, retirar **ambas** entradas `MRS_ADMIN_USERNAME` y `MRS_ADMIN_PASSWORD_HASH` del panel de Secrets. La cuenta y su hash ya están en PostgreSQL. El bootstrap no sobrescribe administradores existentes.

`APP_PASSWORD` puede conservarse como configuración para una reversión temporal. Con `MRS_AUTH_MODE = "accounts"` no concede acceso ni privilegios. Para volver expresamente a la clave compartida, cambiar `MRS_AUTH_MODE = "shared"`; esto no elimina los registros de PostgreSQL, pero esa modalidad no identifica a residentes ni registra progreso individual.

## Generación e interpretación con IA

La aplicación reutiliza `OPENAI_API_KEY` y `OPENAI_MODEL` guardados en Secrets. Opcionalmente, `MRS_GENERATOR_MODEL` permite especificar otro modelo compatible con Responses y Structured Outputs para preparar los encuentros. No es necesario cambiar el modelo ya configurado.

Cada nuevo encuentro hace como máximo una solicitud de generación, con límite de salida y tiempo de espera. Reanudar el mismo encuentro usa su estado guardado. Si la solicitud falla o no cumple el esquema, se utiliza una variante local. El registro docente conserva la procedencia. La interpretación de las intervenciones sigue usando su flujo independiente.

Se verificó la implementación con la [documentación oficial de Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs). En esta entrega se probaron respuestas del proveedor simuladas; no se hizo una llamada facturable con la clave de tu despliegue. Al activarlo, revisar la procedencia `spec.provenance.source` de un caso docente: `ai` indica una composición aceptada; `fallback` indica una variante local.

## Prueba local desde Downloads

El ZIP completo contiene la carpeta `management_reasoning_simulator_v0.10.0`.

```bash
cd ~/Downloads
unzip management_reasoning_simulator_v0.10.0.zip
cd management_reasoning_simulator_v0.10.0
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup_accounts.py --local-db "$PWD/local-data/accounts.sqlite3"
export MRS_AUTH_MODE=accounts
export MRS_ALLOW_LOCAL_SQLITE=true
export MRS_DATABASE_URL="sqlite:///$PWD/local-data/accounts.sqlite3"
streamlit run app.py
```

SQLite guarda los datos en ese equipo y se permite únicamente como prueba local explícita. En Streamlit Cloud se requiere PostgreSQL porque el disco de la aplicación no ofrece esa persistencia. No subir la carpeta `local-data` ni archivos de Secrets.

## Comprobación y límites de la entrega

```bash
pip install pytest
python run_regressions.py
python -m pytest test_account_store.py test_account_portal.py test_encounter_generator.py test_curriculum_assignment.py test_curriculum_trajectories.py test_curriculum_app.py -q
```

Las pruebas cubren aislamiento entre usuarios, roles, invitaciones de un solo uso, expiración y revocación, persistencia local real, conflictos de guardado entre pestañas, recorrido Streamlit, caso congelado, cardioversión, reevaluación y ECG. PostgreSQL está soportado por el código, pero aún debe verificarse contra la base concreta del despliegue. No se ha realizado una prueba de carga concurrente ni validación clínica o psicométrica.

Si aparece un conflicto entre pestañas, la aplicación conserva los cambios locales y ofrece reintentar o descartar los cambios sin guardar de esa pestaña para reabrir el estado persistido. No sobrescribe silenciosamente el trabajo de otra sesión.

El [alcance curricular y las referencias](CURRICULUM_PILOT.md) detallan los tres desafíos disponibles y las limitaciones de los perfiles. Los restantes desafíos de la matriz son desarrollo pendiente.
