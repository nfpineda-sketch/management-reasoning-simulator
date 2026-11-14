# 02 · Preparación de la persona operadora (un revisor, un proceso, un disco local)

*Alcance: UN revisor docente, UNA cuenta docente individual, UN proceso local y UN almacén en disco local. No se generaliza la arquitectura de despliegue.*

## 1 · Requisitos
- El repositorio en `phase-3-runtime-integration` (publicado en `e6f848f` o posterior que **no cambie** el código certificado) y sus dependencias (`pip install -r requirements.txt`).
- Un equipo con **disco local** (no una carpeta de red, nube sincronizada ni NFS). **No** Streamlit Community Cloud.
- Elige un código de revisor, p. ej. `R1`. Carpetas **fuera del repositorio**:
```bash
mkdir -p "$HOME/faculty_review/R1/store" "$HOME/faculty_review/R1/accounts"
chmod 700 "$HOME/faculty_review" "$HOME/faculty_review/R1"
```
- Para el ensayo usa **otro** código (`R0`): **nunca** ensayes en el almacén del revisor.

## 2 · Cuenta de administración (sólo tú)
```bash
python setup_accounts.py --local-db "$HOME/faculty_review/R1/accounts/accounts.sqlite3"
```
Pide un usuario y una contraseña (mínimo 12 caracteres, sin mostrarla). **Guárdala tú; no se comparte ni se escribe en el repositorio.**

## 3 · Invitación docente (arranque normal, sin variables de revisión)
```bash
export MRS_AUTH_MODE=accounts MRS_ALLOW_LOCAL_SQLITE=true
export MRS_DATABASE_URL="sqlite:///$HOME/faculty_review/R1/accounts/accounts.sqlite3"
streamlit run app.py
```
Entra como administrador → barra lateral **Account administration** → `Invite role` = `faculty` → `Create invitation` → copia el código y entrégalo **en privado** a la persona revisora (se usa una sola vez). Detén el proceso (Ctrl+C). *(Verificado en un navegador real.)*

## 4 · Arranque del entorno de revisión (UN proceso)
```bash
export MRS_FACULTY_DEVELOPMENT_REVIEW=faculty_development_review
export MRS_PHASE3_SHADOW=shadow_compare
export MRS_PHASE3_AUTHORITY=limited_common_authority
export MRS_PHASE3_AUTHORITY_SNAPSHOT=gi_pressure_committed
export MRS_PHASE3_AUTHORITY_ENVIRONMENT=development
export MRS_OFFLINE_CASES=1
export MRS_PHASE3_AUTHORITY_STORE="$HOME/faculty_review/R1/store"
export MRS_AUTH_MODE=accounts MRS_ALLOW_LOCAL_SQLITE=true
export MRS_DATABASE_URL="sqlite:///$HOME/faculty_review/R1/accounts/accounts.sqlite3"
streamlit run app.py
```
- **Las variables van en el entorno del proceso, nunca en el archivo de Secrets** (no se honran allí).
- **Un solo proceso**: un segundo proceso sobre el mismo almacén se niega (`single_process`). Si necesitas reiniciar, detén el primero.
- Si falta una condición, la página no lanza nada y la persona docente ve las razones (`FACULTY DEVELOPMENT REVIEW UNAVAILABLE`).

## 5 · La persona revisora entra
Abre la dirección que imprime Streamlit, pestaña `Create account` con el código de invitación, un usuario **no identificable** (p. ej. `revisor1`) y **su propia** contraseña. Debe ver **Faculty development review** y el aviso amarillo.

## 6 · Ensayo previo (con `R0`, otro almacén y otra base de cuentas)
1. Repite 1 a 4 con `R0`. 2. Entra, corre **FR-B** completo (hoja de autoridad), crea el paquete (`Create review bundle` → `stored: True`) y sal (`☰ Menu` → `End this attempt without completing review`). 3. Corre **FR-F** hasta la parada y sal con `Exit the experimental encounter`. 4. Ejecuta el resumen (§8) sobre `R0` y comprueba que dice **COINCIDE** con el guion y que el artefacto verifica y se repite. 5. Borra la carpeta `R0`. **No guardes respuestas de ensayo** en el almacén real.

## 7 · Durante la sesión
No orientes el juicio, no abras la hoja del comparador antes de que la persona revele, no contestes por ella. Anota en el registro (07) el código de cada paquete y de cada `Feedback stored`, y cualquier incidente técnico. Si la pantalla difiere de la hoja de autoridad, anótalo.

## 8 · Cierre y resumen técnico (sólo lectura)
Detén el proceso (Ctrl+C) y haz **copia** de la carpeta `R1/store/faculty_review/` (paquetes y retroalimentación) y de las hojas de papel. Luego:
```bash
python3 faculty_review_kit/tools/session_summary.py --store "$HOME/faculty_review/R1/store" --reviewer R1 --out "$HOME/faculty_review/R1/resumen_R1.md"
```
Sale con código 0 si lo técnico es consistente y 2 si hay un hallazgo (se lista). **No puntúa ni interpreta**: tabula las respuestas tal cual.

## 9 · Si algo falla
Consulta `10_notas_facilitador.md`. Si el proceso muere a mitad de un encuentro, al volver a entrar verás `UNFINISHED ATTEMPT` (el entorno nunca retoma): pulsa `Abandon the unfinished attempt`; lo no enviado se perdió y se anota.

## 10 · Lo que NO se hace
No desplegar varias instancias ni usar discos de red; no firmar ni cifrar registros (limitación declarada: el registro y el ancla no están firmados); no cambiar guiones, escenarios ni trayectorias; no usar residentes; no usar la cuenta de otra persona; no editar a mano los registros.
