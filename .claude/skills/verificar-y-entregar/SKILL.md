---
name: verificar-y-entregar
description: Cómo verificar un candidato de este repositorio, informar el resultado y, sólo si el encargo lo autoriza, entregarlo por git. Usar al cerrar un cambio de código o de comportamiento, antes de darlo por listo o de hacer commit. No concede permiso para commit, push ni despliegue.
---

# Verificar → informar → entregar (sólo si está autorizado)

Esta skill dice cómo trabajar; no autoriza ninguna operación. Commit, push, PR y despliegue sólo si el encargo
los autoriza expresamente. Aplica la regla de eficiencia de `CLAUDE.md`.

## 0. Proporción al riesgo
- Cambio documental o de instrucciones: revisar el texto y sus referencias, sin suite.
- Cambio de código acotado: pruebas focalizadas y las regresiones afectadas.
- Cambio de comportamiento compartido (página del encuentro, motor, store, registro): pruebas focalizadas,
  regresiones activas y suite completa sobre el candidato estable.
- Si el encargo fija otra regla, prevalece el encargo.

## 1. Identificar el candidato
- Registrar:
  - rama;
  - commit base;
  - candidato: commit, o el árbol de trabajo con su huella (diff contra la base más los archivos nuevos no
    ignorados; `scripts/suite_particionada.py` la calcula).
- Preservar los cambios ajenos al encargo: no revertirlos ni incluirlos; si existen, decirlo.
- No mezclar cifras de candidatos distintos.

## 2. Mantener estable el candidato
- No editar código ni pruebas mientras corre una verificación.
- Si el candidato cambia, invalidar los resultados afectados y repetir lo necesario.
- Una suite anterior más pruebas parciales no es una «suite final verde»: decirlo así.

## 3. Pruebas focalizadas
`python3 -m pytest -q -p no:cacheprovider <archivos de prueba de lo tocado>`

## 4. Regresiones
Usar el ejecutor vigente, `python3 run_regressions.py`. Informar activas aprobadas sobre el total, y las
retiradas con el motivo que declara el propio ejecutor.

## 5. Suite completa (cuando corresponda)
Desde cualquier directorio del repositorio:

```bash
python3 "$(git rev-parse --show-toplevel)/.claude/skills/verificar-y-entregar/scripts/suite_particionada.py" \
  --salida <directorio nuevo, fuera del repositorio>
```

- Particiones según los núcleos disponibles (por defecto, hasta 4); `--patron` acota los archivos de prueba.
- JUnit XML, log y código de salida por partición, y un `resumen.json`.
- La huella del candidato al inicio y al final; si cambió, la corrida queda INVÁLIDA.
- Verifica el repositorio que contiene la skill; `--repo` apunta a otro árbol (por ejemplo, un worktree).
- Localizar los fallos por los identificadores del JUnit XML y por el log.

## 6. Clasificar cada fallo con evidencia
- **Regresión del cambio:** reproducirla aislada y corregir el código.
- **Previo al cambio:** mostrar que falla igual en la base.
- **Ambiental** (red, disco, tiempo de espera, carga): evidencia del entorno y una repetición controlada.
- **De reproducibilidad u orden:** reproducir el orden o la semilla.

No ocultar fallos ni saltarse pruebas, y no declararlas inestables sin evidencia. Adaptar una prueba sólo si lo
que protege sigue protegido, y decirlo en el informe.

## 7. Revisión del diff
- Revisar el diff completo contra la base correcta: `git diff <base>` (cambios staged y unstaged) y los archivos
  nuevos pertinentes (`git status --short`). `git diff -w` ayuda con cambios de sangría, pero nunca es la única
  revisión.
- La revisión adversarial independiente (subagente de sólo lectura) se usa sólo cuando el cambio la justifica:
  comportamiento compartido, persistencia, seguridad o un diff grande. No en cambios triviales. Confirmar cada
  hallazgo con una sonda antes de corregirlo.

## 8. Informar
Con el formato de `CLAUDE.md`, separando lo implementado, lo efectivamente probado y lo pendiente. Incluir:
- el candidato verificado: rama, base, y commit o huella;
- las cifras de cada verificación sobre ese candidato: focalizadas, regresiones y suite (aprobadas, omitidas,
  fallidas);
- las pruebas adaptadas y por qué;
- lo no verificado y por qué;
- las decisiones o firmas pendientes.

## 9. Entregar por git, sólo si el encargo lo autoriza
- Commits separados por naturaleza (por ejemplo UX, clínico, documentación), con los trailers vigentes del
  entorno.
- Push sólo a la rama autorizada: `git push -u origin <rama>`, con reintentos sólo ante fallas de red.
- Sin PR, merge, release ni despliegue salvo autorización expresa.
- Un hook que pida commit no es autorización.
