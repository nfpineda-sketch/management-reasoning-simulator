# P3-INTEGRATE-AMEND1 · Diseño de la integración de la enmienda certificada en la Fase 3

**Sólo diseño. No se ejecuta sin autorización expresa.** Este documento vive en la rama
`phase-2-amendment-1-respiratory-transmission`; `phase-3-runtime-integration` no se toca en este paquete.

> **EJECUTADO el 2026-11-10, con autorización expresa (FD-P3-118, FD-P3-119).** Caso A: revert del revert
> `601452c` y merge sin *fast-forward* `534aa50` de la promoción `0c230f8`; el árbol integrado es el mismo objeto
> que el de `0c230f8`. Sin *force push* y sin PR. El texto de abajo queda como se escribió, en futuro, porque es
> el diseño que se autorizó.

## 1 · De dónde se parte

| Rama | Cabeza | Qué contiene |
|---|---|---|
| `phase-3-runtime-integration` | `e1eb797` | … `258e71f` → `d087cc3` (enmienda sin certificar) → `e1eb797` (**revert** de `d087cc3`; su árbol es el de `258e71f`) |
| `phase-2-amendment-1-respiratory-transmission` | la cabeza de promoción de este paquete | … `258e71f` → `d087cc3` → `da931a9` (forense) → puntos de control → candidato congelado → promoción |

La base común de las dos ramas es **`d087cc3`**. Lo que la Fase 3 hizo desde esa base es **deshacerla**.

## 2 · La trampa que hay que evitar: un `merge` directo PIERDE la enmienda

Con base `d087cc3`, un merge de tres vías ve dos historias: la Fase 3 **quitó** el contenido de `d087cc3`; la rama
de la enmienda **lo modificó sólo en parte**. Para todo lo que `d087cc3` añadió y la enmienda no volvió a tocar
(por ejemplo la declaración del campo en `derived.py`, o `respiratory_transmission_record.py`), git toma el lado
de la Fase 3 —el revert— **sin conflicto y en silencio**. El resultado compilaría a medias y no sería el núcleo
certificado. Es el caso conocido de «volver a integrar una rama cuyo merge se revirtió».

Tampoco sirve un *squash* o un *cherry-pick* del diff: el resultado tendría el contenido correcto, pero la cabeza
certificada **no sería antecesora** de la Fase 3 y el registro del linaje apuntaría a commits ajenos a su historia.

## 3 · Procedimiento propuesto (sin reescribir historia, sin *force push*)

**I0 · Comprobaciones previas (sólo lectura).**
- `git fetch`; anotar la cabeza de ambas ramas; confirmar que no hay trabajo ajeno superpuesto.
- La rama de la enmienda dice `CERTIFIED` en `docs/revision/PHASE2_AMENDMENT_1.json` y la compuerta real da `ok`
  **sin** el plugin de vista previa.
- Listar los commits de la Fase 3 posteriores a `e1eb797` (hoy, ninguno) y qué archivos tocan. Los que toque
  también la enmienda (`runtime_shadow.py`, `runtime_shadow_evidence.py`, `runtime_authority.py`, `conftest.py`,
  y los fixtures de unas 45 pruebas) son la superficie de conflicto real.

**I1 · Rama de integración.** `git switch -c p3-integrate-amend1 origin/phase-3-runtime-integration`. Nunca se
trabaja directamente sobre `phase-3-runtime-integration`.

**I2 · Revertir el revert.** `git revert --no-edit e1eb797`. Deja un commit nuevo que restaura el contenido de
`d087cc3` y conserva `e1eb797` en la historia. Verificación: si no hay commits posteriores de la Fase 3, el árbol
debe ser **el mismo objeto** que el de `d087cc3` (`git rev-parse HEAD^{tree}` = `git rev-parse d087cc3^{tree}`).

**I3 · Merge de la rama certificada.** `git merge --no-ff origin/phase-2-amendment-1-respiratory-transmission`.
Tras I2 el cambio neto de la Fase 3 respecto de la base es nulo, así que el merge trae limpia toda la historia de
la enmienda. La cabeza de certificación queda como antecesora.

**I4 · Identidad del resultado.**
- **Caso A (sin commits propios de la Fase 3 después de `e1eb797`, el de hoy):** el árbol de la cabeza de
  integración debe ser **el mismo objeto** que el de la cabeza certificada de la enmienda. Si lo es, la
  certificación se traslada por identidad de árbol —el mismo argumento con el que se aceptó la restauración
  `e1eb797` ≡ `258e71f`— y basta una comprobación corta (I5). Si **no** lo es: STOP e investigar.
- **Caso B (la Fase 3 avanzó):** los árboles difieren por construcción. Se resuelven los conflictos a mano, con
  la regla «lo certificado no se edita para acomodar; lo nuevo de la Fase 3 se adapta al linaje», y se corre una
  certificación completa nueva sobre la cabeza de integración.

**I5 · Verificación sobre la rama de integración (sin plugin de vista previa).**
1. `clinical_core` recalcula al digesto de la enmienda y el cierre histórico (`22b90a6f…`) se reconstruye.
2. `core_lineage_verdict()` da las cuatro condiciones en verdadero; `versions()` nombra `PHASE2_AMENDMENT_1`.
3. `test_phase2_amendment*.py`, `test_phase2_closure.py`, las 16 pruebas de etapa de la cadena y las 14 de la
   capa de la Fase 3.
4. Regresiones (`python3 run_regressions.py`), aislamiento y congelamiento del lector.
5. Suite completa: obligatoria en el caso B; en el caso A, decisión docente (la identidad de árbol la hace
   redundante, pero cuesta ~40–80 min y deja una evidencia propia de la rama).

**I6 · Publicación.** `git push origin p3-integrate-amend1`; con la verificación en verde y autorización,
avance *fast-forward* de `phase-3-runtime-integration` a esa cabeza (`git merge --ff-only`). Push normal.

## 4 · Qué cambia para la Fase 3 al integrar

| Aspecto | Antes (`e1eb797`) | Después |
|---|---|---|
| Compuerta de digesto | `phase2_digest_now() == PHASE2_DIGEST` | cuatro condiciones del linaje certificado |
| `clinical_core` | 141 fuentes, digesto `22b90a6f…` | 142 fuentes, digesto de la enmienda; el cierre se reconstruye por reversión |
| `versions()` | identidad del cierre | además `core_version` y `core_digest` del núcleo activo |
| `phase3_layer_digest` | el de `e1eb797` | cambia: tres fuentes de la capa se editaron. La evidencia guardada con el digesto anterior queda fechada en la capa anterior, como en cualquier cambio de capa |
| Perfiles comprometidos | sin el control | el control existe y vale `None` en todos: ninguna lectura se mueve |
| Autoridad | `COMMON_CORE_RUNTIME_AUTHORITY = False` | **igual**. La enmienda no concede autoridad |
| Lo que ve el residente, puntuación, piloto | — | **sin cambio** |

Documentos a actualizar **en el mismo paquete de integración** (no ahora): la viñeta de la Fase 2 de `CLAUDE.md`
(hoy dice que el digesto de cierre cubre las 141 fuentes: hay que añadir que el núcleo vigente es un sucesor
certificado del linaje), `docs/PHASE3_RUNTIME_INTEGRATION.md` y las filas del Decision File.
`validation/BASELINES.md` no se toca.

## 5 · Lo que la integración NO incluye

- **Usar** el control. Declarar una fracción en un perfil de familia (la región medida en P3-128 es
  `f ≤ 0,060621`, con R = 0,8 declarado y sólo el cociente f/R identificado) es una decisión docente aparte y un
  paquete aparte. Integrar la enmienda sólo deja el control **disponible y apagado**.
- Autoridad de ejecución para el núcleo común, cambios en la pantalla del residente o en la puntuación.
- Compatibilidad hacia adelante de artefactos: un artefacto escrito por el núcleo enmendado lleva la clave nueva
  y el núcleo del cierre lo rechaza. No se promete lo contrario.

## 6 · Riesgos y cómo se detectan

| Riesgo | Detección |
|---|---|
| Merge directo sin I2 (pérdida silenciosa) | I4: el árbol no coincide con el certificado; la compuerta falla en `active_core_in_lineage` |
| Conflictos en fixtures de pruebas si la Fase 3 avanzó | I0 los enumera antes de empezar |
| Alguien deja activo el plugin de vista previa | tras la promoción no cambia nada; la prueba de linaje exige que nada lo cargue |
| Evidencia de la Fase 3 guardada con el digesto de capa anterior | declarado en la tabla de §4; no se reescribe |
| Volver atrás | `git revert -m 1 <merge>` y luego `git revert <revert-del-revert>`: se vuelve al árbol de `e1eb797`. Una reintegración posterior tiene otra vez la trampa de §2 |

## 7 · Decisiones que necesita quien autorice

1. Autorizar o no `P3-INTEGRATE-AMEND1` con este procedimiento.
2. En el caso A, si la identidad de árbol basta o se quiere además una suite completa propia de la rama.
3. Si el avance de `phase-3-runtime-integration` se hace por *fast-forward* directo o mediante PR.
