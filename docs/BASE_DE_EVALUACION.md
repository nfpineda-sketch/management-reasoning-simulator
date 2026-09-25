# La base de evaluación de cada encuentro

Instrucción docente del 2026-09-25, puntos 7, 8 y 10. Módulo: `evaluation_basis.py`.

## Qué se congela y dónde

Al iniciar un encuentro (`curriculum_runtime.start_encounter`) se guarda, junto con el resto del encuentro,
`encounter["evaluation_basis"]`:

- **Declaraciones:** las oportunidades por dominio, los eventos críticos con sus ventanas, alternativas y
  exclusiones, la información disponible y los límites del motor. Es una copia completa de lo que el caso
  declara ese día.
- **Versiones:** cobertura de las declaraciones, rúbrica y motor (`family_engine`). Si el caso es del
  catálogo, además la versión del catálogo, la configuración, su firma clínica, su huella y la versión de
  `glucose_rescue`.
- **Código y momento:** el commit (`code_version`) y la hora.
- **Huella:** permite detectar una copia alterada.

La columna del encuentro se escribe una sola vez: el almacén de cuentas no tiene cómo actualizarla. El análisis
(tamizaje, propuesta de rúbrica, revisión docente, revisión de la historia) y la regeneración de documentos
leen esa copia, no las declaraciones actuales del código.

## Un estado por registro

| Estado | Qué es | Qué muestra |
|---|---|---|
| `frozen` | El encuentro trae su copia | Nada adicional |
| `legacy` | Un caso del banco guardado antes de que existieran las copias | Se evalúa con las declaraciones vigentes hasta el 2026-09-25 (`evaluation_bases/coverage_1.0_legacy.json`, cobertura 1.0) y dice que la versión vigente al iniciarlo **no se puede verificar**. No se le atribuye ninguna versión verificada |
| `unfrozen_current` | Sin copia y desconocido para esa instantánea | Declaraciones actuales, dicho así |
| `generated` | Caso generado (`AI-…`) | No hubo declaraciones: no se muestran oportunidades ni eventos, no se inventan ceros ni un total completo o comparable; los cinco dominios se pueden puntuar desde el registro |
| `no_authored_case` | El encuentro no nombra un caso | Igual que antes: los cinco dominios, sin eventos |
| `unknown_case` | Nombra un caso que ninguna declaración conoce | Error visible: «identificador inválido» |
| `corrupt` | El registro o su copia no se pueden leer, o la copia no coincide con su huella | Error visible, con el motivo |

Ninguno de estos estados cierra el panel de la rúbrica ni los documentos del encuentro.

## El fallo que se corrigió

Un caso generado se identifica `AI-…`. Hasta el 2026-09-25, `case_assessment` lanzaba `CoverageError` al buscarlo,
y nadie la capturaba en la rúbrica, el tamizaje, la propuesta ni la revisión de la historia. Abrir la rúbrica o
el análisis de un encuentro generado interrumpía el circuito. Ahora el registro resuelve su estado y se informa
la limitación.

Lo comprueba `test_generated_case_evaluation.py` con un caso generado por un autor simulado, sin proveedor y
sin pago: el portal, el tamizaje, la propuesta, la revisión y el documento de la rúbrica funcionan. Un evento
crítico sobre un caso sin declaraciones se rechaza.

## La instantánea de los registros antiguos

`evaluation_bases/coverage_1.0_legacy.json` es la copia exacta de todas las declaraciones al commit d184845, con
su huella. Para todos los casos coincide con el código de hoy, salvo `hypoglycemia_54m_thiamine`, cuya versión
1.1 cambió (`docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md`, DC7). Por eso ningún encuentro anterior se juzga
distinto por este cambio: los de la 54m conservan `hypo_no_thiamine`.

## Reevaluar con criterios nuevos

`evaluation_basis.reevaluation(record, reason=..., requested_by=...)`:

- exige un motivo y una persona;
- devuelve una base nueva que nombra la anterior (estado, huella y versiones);
- no guarda nada ni reemplaza la copia con que se inició el encuentro;
- nunca toca una decisión docente confirmada: quien guarde un análisis hecho con ella conserva las dos.

Todavía no tiene pantalla.

## Preparado para las etapas siguientes (sin usarse aún)

Cada lanzamiento registra además, en `encounter["assignment"]`:

- `purpose: "practice"`: una evaluación con condiciones conocidas todavía no existe;
- `exposure`: los encuentros completados de la misma cuenta con el mismo caso y con la misma firma clínica
  (las condiciones que deciden el caso, no la superficie), con su marca de sandbox.

Con eso, más la base congelada y el contexto de asistencia que ya se declara, una etapa posterior puede:

- priorizar configuraciones no vistas;
- registrar repeticiones deliberadas con su motivo;
- decidir comparabilidad con asistencia, exposición previa y contexto de ejecución, no sólo con configuración y
  versión;
- agrupar el historial longitudinal por versiones compatibles.

Nada de eso está implementado ni se usa para elegir casos.
