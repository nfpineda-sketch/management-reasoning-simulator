# Ejecutar la tanda de 20 desde un computador

La tanda se ejecuta desde un computador con red directa. Una sesión en la nube de
Claude Code no puede: la página de Streamlit necesita un WebSocket y el proxy de esas
sesiones no lo admite (`docs/TANDA_20_ESCENARIOS.md` §4). Esta guía es para una sesión
local de Claude Code en el computador del administrador, o para una persona en una
terminal.

## 1. Preparar

```
git clone https://github.com/nfpineda-sketch/management-reasoning-simulator
cd management-reasoning-simulator
git checkout clinical-encounter-v0.13
python3 --version            # 3.11 o superior; si no, instalarlo desde python.org
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python -m playwright install chromium
```

## 2. Las contraseñas

Nunca en el chat ni en un archivo que se suba al repositorio. El administrador crea,
en la carpeta del repositorio, el archivo `local-data/tanda20/credentials.env`
(`local-data/` nunca se sube) con tres líneas:

```
MRS_BATCH_RESIDENT_PASSWORD=<contraseña de residente_prueba_r3>
MRS_BATCH_STAFF_USER=<usuario de la cuenta docente de prueba>
MRS_BATCH_STAFF_PASSWORD=<contraseña de la cuenta docente de prueba>
```

El ejecutor también acepta esos nombres como variables de entorno, que tienen
prioridad. Nada los imprime. Después de la tanda: borrar el archivo y cambiar las dos
contraseñas.

## 3. Verificación previa (gratis)

```
python tools_tanda20.py --preflight --base-url https://clinical-management-reasoning-dev.streamlit.app
```

Inicia sesión con las dos cuentas y sólo lee la página. Todo tiene que salir `ok`.
Si sale `MISSING`, dice qué falta; si Streamlit pide su propio inicio de sesión, la app
es privada en Streamlit Community Cloud y el administrador decide si la deja visible
para quien tenga el enlace durante la tanda (el simulador sigue exigiendo sus cuentas).
Además, en los Secrets de la app debe estar `MRS_SYNTHETIC_ACCOUNTS = "residente_prueba_r3"`:
la verificación previa no puede comprobarlo.

## 4. La tanda (pagada)

```
python tools_tanda20.py --run 1 --base-url https://clinical-management-reasoning-dev.streamlit.app
```

y así con 2, 3… 20, en español, uno por uno, revisando cada resultado antes del
siguiente. Cada escenario dirige el caso con la cuenta docente de prueba, lo juega
como `residente_prueba_r3` por la página, cierra, reflexiona, declara la prueba
sintética y genera los cuatro documentos; queda una línea en
`local-data/tanda20/batch/ledger.jsonl`. En macOS, `caffeinate -i` antes del comando
evita que el computador se duerma a mitad de un escenario.

Reglas (especificación del 2026-09-24):

- Como máximo **40 encuentros pagados** en total, reintentos incluidos; van 0. Si no se
  completan los 20 dentro de ese límite, detenerse y entregar el número exacto
  conseguido, los bloqueos y lo hecho. La versión en inglés (`--language en`) no se
  corre sin autorización expresa.
- Todas las evaluaciones (rúbrica y challenges) quedan **pendientes** de revisión del
  administrador: no se confirma nada y no se atribuye ninguna aprobación a un docente
  real. Todo se identifica como prueba sintética de un agente en una cuenta de prueba.
- Nunca insertar encuentros ni registros directamente en la base; nunca marcar como
  completo algo que no lo está; no cambiar reglas clínicas ni criterios educativos para
  que algo pase.
- Si un escenario se detiene, diagnosticar la causa. Si hay que corregir código:
  `python -m pytest -q` y `python run_regressions.py` antes de subir nada.
- **No subir nada a la rama durante la tanda**: la app de desarrollo se redespliega al
  recibir un envío y cortaría el encuentro en curso. Commits locales, y un solo envío a
  `clinical-encounter-v0.13` al terminar.
- No fusionar a `main`, no tocar la app pública, no enviar nada a terceros (los ejemplos
  para Nate quedan preparados, no enviados).

## 5. Al terminar

Completar el índice de intentos (`docs/TANDA_20_ESCENARIOS.md` §6) y el registro
(`docs/AVANCE_2026-09-24.md`), hacer commit y subir a `clinical-encounter-v0.13`.
Informe en español: encuentros completados y su identificador, documentos A-D
recuperables, evaluaciones pendientes visibles desde la cuenta de administrador,
encuentros pagados consumidos, problemas y cómo se resolvieron, bloqueos pendientes; lo
verificado por la interfaz separado de lo verificado con pruebas internas.
