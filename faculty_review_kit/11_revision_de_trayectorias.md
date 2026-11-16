# 11 · Revisión de trayectorias (el camino principal; 3–5 minutos por escenario)

**Qué es.** Juzgas trayectorias de presión que ya existen y están certificadas. **No** juegas ningún encuentro, **no** abres archivos, **no** copias códigos. Los archivos `01`–`10` y `paquetes/` describen el modo *en vivo*, que sigue disponible («Review mode → Live review encounter (advanced)») para más adelante.

## Qué haces (por escenario)
1. Entra con tu cuenta docente. Desde P3-352 la aplicación abre por omisión la **re-revisión** (`12_rerevision_interactiva.md`), no esta. Para esta primera revisión abre el desplegable «Review mode» y elige **Trajectory review (first review)**; verás la pantalla **Faculty Trajectory Review** con el primer escenario (**FR-B**). Si ves el selector «Review encounter», es el modo en vivo: elige **Trajectory review** en el mismo desplegable.
2. Lee el **contexto**, la **línea de tiempo** (qué se hizo y cuándo) y la **trayectoria** (los números en el gráfico, PAS/PAM/PAD). Los números en gris marcan las intervenciones de la tabla.
3. Contesta **Q1–Q5** (una pulsación cada una). En los escenarios donde el experimento se detiene hay una pregunta más (**Q5H**). Tus respuestas se guardan solas: si refrescas o cierras el navegador, al volver están ahí.
4. Pulsa **LOCK FIRST IMPRESSION & REVEAL COMPARATOR**. Desde ese momento tu primera impresión queda fija y nadie puede cambiarla. Aparece el comparador heredado sobre los mismos ejes (línea discontinua), rotulado «Legacy comparator — nonauthoritative comparison». **No es la verdad ni un estándar de referencia**: es contexto para tu juicio.
5. Contesta «¿Ver el comparador cambió tu juicio?» y el **juicio global** (ACCEPT / ACCEPT_WITH_LIMITATION / RECALIBRATE / REJECT). Comentarios: opcionales, sin datos de pacientes reales.
6. Pulsa **Submit and continue**. Pasas **sola/solo** al siguiente escenario.

Al terminar los **cinco** obligatorios (FR-B, FR-A, FR-E, FR-G, FR-F) aparece **REVIEW COMPLETE** con el recuento de tus juicios y tus comentarios. FR-D y FR-C son **opcionales**. No hay formulario de papel, ni hoja de comparador, ni archivo de cierre: el resumen técnico se crea solo.

## No tienes que
Copiar códigos de paquete o de retroalimentación · abrir `.md` · buscar un panel oculto · salir por un menú especial · rellenar `08_resumen_fin_de_sesion.md`.

## Notas
* **Tiempo:** ≈ 4 min por escenario es una **estimación** de quien escribió esto; no se ha medido con una persona.
* **Pantallas con «Stop»:** en FR-A, FR-D y FR-F el experimento se detiene por un límite **operativo** del entorno, no por un resultado del paciente.
* **Si refrescas el navegador:** la aplicación te pide iniciar sesión otra vez (así funciona con cuentas individuales); al volver, tus respuestas guardadas están ahí.
* **Ya enviado, no se edita:** un escenario enviado se puede **ver** desde la barra superior (✓), no cambiar.
* **Operador:** arranque y proceso único como en `02_preparacion_operador.md`. El resumen técnico se escribe en `<almacén>/faculty_review/trajectory/session_summary_<ref>.json`; los registros, en `<almacén>/faculty_review/trajectory_reviews/`. Ningún dato de revisión entra al repositorio.
