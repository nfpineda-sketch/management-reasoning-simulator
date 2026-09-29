# Respaldo y restauración de la base del piloto

Ciclo 10, tarea C10-05 (2026-09-29). Cómo respaldar y restaurar la base de la aplicación, y la prueba
de que el procedimiento no pierde nada. **No se usó ningún dato real:** el simulacro corrió sobre bases
desechables, con los datos de la prueba de humo.

## Qué se respalda

Todo el estado de la aplicación vive en la base de `MRS_DATABASE_URL`: 33 tablas `mrs_*`. Incluyen:

- cuentas, invitaciones y sesiones;
- encuentros con su Trace;
- rúbricas, evidencia, portafolio y observaciones;
- fotos aprobadas, con sus archivos;
- directivas docentes y el historial de cambios de cuentas.

Un respaldo es, por eso, **información de residentes**: se guarda cifrado, fuera del servidor, con acceso
restringido, y **nunca** en el repositorio.

## Procedimiento (PostgreSQL, el motor de un despliegue)

1. **Respaldar**, antes de cada despliegue o cambio de versión, y a diario mientras dure el piloto:

   ```
   pg_dump --format=custom --no-owner --no-privileges --file=mrs-AAAAMMDD-HHMM.dump "$MRS_DATABASE_URL"
   ```

2. **Guardar** el archivo fuera del servidor, cifrado y con acceso restringido.
3. **Restaurar** en una base **vacía**, nunca sobre la que está en uso:

   ```
   pg_restore --no-owner --no-privileges --exit-on-error --dbname="$URL_DE_LA_BASE_NUEVA" mrs-AAAAMMDD-HHMM.dump
   ```

4. **Verificar** que la copia es idéntica. Este paso sólo lee ambas bases e imprime, por tabla, los
   conteos y si las filas coinciden; nunca su contenido.

   ```
   python3 tools_backup_drill.py --compare "$MRS_DATABASE_URL" "$URL_DE_LA_BASE_NUEVA"
   ```

5. **Volver a la copia**, si hace falta: apuntar `MRS_DATABASE_URL` a la base restaurada y reiniciar la
   aplicación. Al abrir, la aplicación no cambia ninguna fila (comprobado abajo).

- **Respaldos del proveedor:** el respaldo automático del proveedor, si existe, no reemplaza una
  restauración de prueba. Haga una antes del piloto, dentro de la condición B del readiness.
- **Versiones:** `pg_dump` debe ser de la misma versión mayor del servidor, o más nueva.
- **SQLite:** sólo para desarrollo local. Use el respaldo en línea:
  `sqlite3 origen.sqlite3 ".backup copia.sqlite3"`.

## El simulacro (2026-09-29)

`python3 tools_backup_drill.py --sqlite` y `--postgres URL` hacen lo siguiente:

1. Llenan una base desechable con lo que escribe el piloto: la prueba de humo en la configuración del
   piloto, una directiva docente y un cambio de cuenta.
2. Toman la huella de cada tabla: filas y hash.
3. Respaldan y restauran en una base nueva.
4. Comparan las huellas tabla por tabla.
5. Abren la base restaurada con los stores de la aplicación y releen cada encuentro.
6. Comprueban que abrirla no cambió ninguna fila.

| Motor | Tablas | Filas | Idénticas tras restaurar | Encuentros releídos | Abrir la copia cambió algo | Respaldo |
|---|---|---|---|---|---|---|
| SQLite | 33 | 691 | Sí, todas | 2 de 2, idénticos | No | Respaldo en línea, 16 MB |
| PostgreSQL 16 (local, desechable) | 33 | 691 | Sí, todas | 2 de 2, idénticos | No | `pg_dump` custom, 11,5 MB, 1,4 s |

**Más resultados:**

- La restauración en PostgreSQL también pasó `--compare` contra su origen, en las 33 tablas.
- Hubo 0 intentos de llamar a un proveedor de IA.
- El clúster PostgreSQL fue local y se borró al terminar.

**Sobre qué código:** el de C10-04 (`fc77a6e`), más las herramientas de este cambio. Sobre el mismo
clúster pasaron las pruebas de PostgreSQL de C10-03 y C10-04 (`test_store_integrity_on_postgres.py`) y
las del banco de imágenes (`test_the_image_bank_on_postgres.py`): 9 de 9.

**Límites:**

- No se probó el respaldo automático de un proveedor concreto ni la restauración a un punto en el tiempo.
- El simulacro no reemplaza la restauración de prueba en el entorno desplegado.
