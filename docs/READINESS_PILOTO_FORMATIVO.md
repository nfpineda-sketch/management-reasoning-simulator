# Readiness del piloto formativo limitado (posterior a V3, 2026-09-29)

Instrucción docente del 2026-09-29 (ampliación no clínica, punto 2). Actualiza
`docs/READINESS_PILOTO_RESIDENCIA.md` (ciclo 9), que queda como estaba.

**Este documento no autoriza nada.** No despliega, no invita residentes, no crea
cuentas reales y no inicia sesiones reales. Dice si el piloto está listo o
bloqueado, y por qué.

## Respuesta

**TÉCNICAMENTE LISTO EN LA VERSIÓN ACTUAL; BLOQUEADO PARA EMPEZAR** por tres
pasos que esta sesión no puede ni debe dar:

1. **La prueba de humo en el entorno real desplegado.** La de abajo corrió en
   la versión real (el commit), en una base local desechable. El despliegue no
   es accesible desde aquí y desplegar no está autorizado. La herramienta
   `tools_pilot_smoke.py` crea su propia base temporal, así que puede correrse
   en el servidor del despliegue sin tocar sus datos.
2. **La configuración del despliegue:** la del piloto (abajo). Con la
   configuración por defecto y una clave del proveedor, abrir un encuentro
   pide una foto al proveedor sin que nadie lo pida.
3. **La autorización docente**, con las aprobaciones humanas pendientes de la
   última sección.

**No es una validación.** La fidelidad del lector con texto externo sigue sin
medirse (B = NOT YET MEASURED); todo juicio lo confirma un docente.

## Prueba de humo (2026-09-29)

**Qué es.** `python3 tools_pilot_smoke.py`: base SQLite temporal, cuentas
propias sin nombres reales, la aplicación real (AppTest de Streamlit). Cada
intento de construir un cliente del proveedor de IA se registra y se rechaza.

**Dónde corrió.** Esta sesión, commit `d0cbeb8` (más la propia herramienta,
aún sin confirmar), `SIMULATOR_VERSION` `0.24.13-clinical-encounter`, motor de
familias 1, ejecución 0.24.2, `glucose_rescue` 2.0, rúbrica `1.0-pilot`,
cobertura 1.1, oportunidades 1.1. **No** en el entorno desplegado.

| Comprobación | Configuración del piloto | Configuración por defecto, con clave |
|---|---|---|
| Residente: abrir, comenzar, ordenar, cerrar, terminar | Sí, sin excepciones (inglés: `opioid_67f`; órdenes en español: `hypoglycemia_28m`) | Sí (`anaphylaxis_29f`; `hypoglycemia_54m_thiamine`) |
| Registro | Encuentro `completed`, Trace con su fila, `code_version` del commit y versiones de su evaluación congeladas | Igual |
| Foco de aprendizaje | Oculto al cerrar; visible para el residente después de la rúbrica confirmada (§154AB) | Igual |
| Revisión docente | Panel docente sin excepción; rúbrica confirmada por el docente | Igual |
| Páginas del residente (encuentros, progreso, portafolio), en inglés y en español | Sin excepciones | Sin excepciones |
| Documento del residente en español | Preparado sin llamar al proveedor | Igual |
| Permisos | Otro residente no lee ni lista el encuentro; el residente no confirma su rúbrica ni crea invitaciones; el docente no crea invitaciones; el docente lee el encuentro | Igual |
| **Intentos de llamar al proveedor** | **0** | **1: la foto de llegada (`image_broker`), al abrir el encuentro** |

**Lo que la prueba encontró y se corrigió antes de terminar:** el panel docente
fallaba («t() got multiple values for argument 'text'») en todo objetivo con
una fila TDFC YES, desde el ciclo 8. Corregido en `d0cbeb8`, con su prueba
(`test_screen_strings_name_their_values.py`). **Ninguna vulnerabilidad de
acceso encontrada.**

**Límites de la prueba.** AppTest no puede hacer clic con las pantallas en
español (busca el valor de un radio traducido entre sus opciones traducidas):
el encuentro en español se jugó con órdenes en español y pantallas en inglés, y
las pantallas en español se renderizaron aparte, sin clics. La reflexión se
escribió en el registro y se guardó por el store, como hace la prueba de la
aplicación completa. Son dos encuentros, no una medición de fidelidad.

## Configuración del piloto

| Variable | Valor | Por qué |
|---|---|---|
| `MRS_OFFLINE_CASES` | `1` | Casos autorados del banco y la clave del proveedor retenida en todas partes: **0 llamadas** medidas. Sin generación de casos ni de fotos, sin análisis por IA |
| `MRS_IMAGE_REQUIRE_REVIEW` | `on` | Sólo fotos con las dos revisiones humanas aprobadas (decisión 8 de imágenes) |
| `MRS_AUTH_MODE` | `accounts` | Cuentas por persona, permisos en los stores |

Con esta configuración **no hay** propuestas de rúbrica por IA, análisis del
Trace por IA ni traducciones a pedido: el docente puntúa y comenta. Habilitar
cualquiera de ellas es una decisión nueva (pregunta abajo).

## Casos, idiomas y versión

- **Casos:** los 31 casos del banco, que el currículo asigna por desafío y año
  de formación. `pulmonary_embolism_61m` **incluido**: corregido y verificado
  (lisis indicada por shock obstructivo desde la llegada, 98/61 a los 45 min).
- **Excluidos:**
  - las 9 composiciones de hipoglicemia (propuestas DC9 pendientes; no se
    exponen);
  - los casos escritos por IA (la configuración del piloto no los genera);
  - PS001/PS002 (motor antiguo, inaccesible).
- **Casos con una limitación que el docente debe conocer** (se juegan igual):
  - `anaphylaxis_63m_betablocked`: el monitor y el ECG muestran FA y el examen
    dice pulso regular (DF-23, fila 7, sin decidir).
  - Casos SCA: el texto de la pared tras reperfundir (DF-23, fila 6).
  - Casos de mujeres en edad fértil, empezando por `pulmonary_embolism_33f`:
    qué responde una prueba de embarazo (DF-23, fila 8).
  - `hypoglycemia_54m_thiamine` y las configuraciones con vía fallida: el
    glucagón o el octreótido por la cánula infiltrada actúan como modelados
    (DC4-F).
  - `bradycardia_bb_54f`: vista neutral; `pulmonary_edema_75f`: la foto V34
    (ambas pendientes).
- **Idiomas:**
  - pantallas en inglés y en español;
  - órdenes en ambos idiomas, con la fidelidad externa sin medir;
  - el relato de cada caso en español sólo si un docente aprobó su traducción
    en la base desplegada. El paquete del repositorio no trae ninguna
    aprobación; en una base nueva el relato se ve en inglés.
  - `acs_70f_left_main` necesita una aprobación nueva: su pasaje cambió.
- **Versión:**
  - cada encuentro congela al empezar su `code_version` (el commit desplegado
    o `MRS_CODE_VERSION`) y las versiones de su evaluación
    (`validation/BASELINES.md`, «Tres versiones distintas»);
  - un encuentro del piloto formativo no es una medición de validación
    externa.

## Supervisión docente

- Cada rúbrica la confirma un docente.
- La IA nunca asigna; no hay puntaje global, ranking ni tabla de posiciones.
- El foco de aprendizaje llega al residente después de la revisión.
- Las limitaciones conocidas son para el docente (`validation/KNOWN_DEFECTS_V3.md`,
  TD-45 en `docs/REGISTRO_DEUDA_TECNICA.md`), no instrucciones para el residente.

## Aprobaciones humanas que faltan

- Autorizar el piloto y su configuración.
- Correr la prueba de humo en el entorno desplegado.
- Si el relato en español se usará: aprobar la traducción de los casos en la
  base desplegada, y de nuevo la de `acs_70f_left_main`.
- Decidir si `anaphylaxis_63m_betablocked` entra con su inconsistencia (DF-23
  fila 7) o espera la decisión.
- Decidir si se habilita alguna función de IA a pedido (propuesta de rúbrica,
  análisis del Trace, traducción a pedido). La configuración recomendada no
  habilita ninguna.
