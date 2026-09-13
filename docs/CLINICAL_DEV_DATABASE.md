# Base persistente de la aplicación clínica de desarrollo

Preparada el 13 de septiembre de 2026 en el proyecto Neon existente
`management-reasoning-simulator` (`lingering-lab-61668857`).

| Recurso | Valor |
|---|---|
| Rama de base de datos | `clinical-encounter-v0.13` |
| ID | `br-bitter-block-auena1gu` |
| Rama de origen | `development-validation` (`br-hidden-morning-aut38evw`) |
| Base | `mrs` |
| Estado de configuración | Esquema preparado; pendiente de conexión desde la configuración privada de Streamlit |

La rama `production` (`br-plain-violet-auc7cg5w`) y la rama de validación no
recibieron escrituras. La nueva rama mantiene los datos separados. No se cambió
la rama predeterminada del proyecto.

Se aplicaron los esquemas derivados de `AccountStore`, `ProgressStore` y
`FacultyBriefStore` y `ManagementTraceStore`, incluidos los campos que congelan el contexto de una
confirmación. Hay 16 objetivos configurados y ninguna cuenta, sesión, invitación,
encuentro, observación o informe docente. No se migraron usuarios ni datos de
residentes de las otras aplicaciones.

## Activación

Desde [Neon Console](https://console.neon.tech), seleccionar el proyecto y la
rama indicados arriba y obtener su conexión **pooled** a la base `mrs`. Configurar
esa URL como `MRS_DATABASE_URL` únicamente en los Secrets de la aplicación de
desarrollo y establecer `MRS_AUTH_MODE = "accounts"`. No guardar la URL en Git,
PDF, ZIP ni documentación pública.

Crear el primer administrador con el flujo de `setup_accounts.py` y los secretos
de bootstrap descritos en [Configuración de desarrollo](RELEASE_v0.17.0.md#activating-individual-accounts-in-development). Aún no se
ha creado un administrador. El residente debe registrarse mediante invitación
como residente; el acceso a los informes docentes depende del rol de personal.

La preparación de esta base por sí sola **no activa** las cuentas en Streamlit.
Es necesario completar la configuración privada de esa aplicación e iniciar
sesión como administrador. Los secretos de las otras aplicaciones se conservan.

## Verificación realizada

- Esquema PostgreSQL aplicado mediante una transacción del conector Neon.
- Campos de confirmación y tablas de informes docentes y análisis del Management Trace presentes.
- Prueba SQL dentro de un savepoint: dos observaciones satisfactorias y una
  insatisfactoria podían coexistir después de una confirmación; su contexto
  original permanecía intacto. Todos los datos de prueba se revirtieron antes
  de confirmar la transacción. Se verificaron cero cuentas, intentos y
  observaciones persistidos y la restauración de la meta local.
- No se pudo ejecutar el cliente Python contra Neon desde este entorno por
  resolución DNS. La comprobación SQL no sustituye una prueba del cliente
  PostgreSQL completo ni una sesión autenticada de la aplicación publicada.
