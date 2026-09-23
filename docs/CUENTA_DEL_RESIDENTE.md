# La cuenta del residente

> Qué guarda, quién la ve, y qué hace el sistema con lo que hay dentro.
> Decisiones docentes del 2026-09-23.

## Lo que la cuenta guarda

| | Dónde vive | Quién lo ve |
|---|---|---|
| Encuentros completados, con su traza | `mrs_attempts` | El dueño y el docente |
| Reflexiones y planes de adaptación | dentro del encuentro | El dueño y el docente |
| Rúbricas **confirmadas** | `mrs_rubric_reviews` | El dueño y el docente |
| Rúbricas en borrador | `mrs_rubric_reviews` | **Sólo el docente** |
| Observaciones de objetivos | `mrs_progress_observations` | El dueño y el docente |
| Foto, iniciales y acuerdo firmado | `mrs_resident_profiles`, `mrs_resident_agreements` | El dueño y el docente |

**Un residente no accede a nada de otro residente.** Ni encuentro, ni puntaje, ni gráfico, ni
foto, ni iniciales. Se hace cumplir en el almacén y no en la pantalla: `list_attempts`,
`get_attempt`, `get_progress`, `RubricStore.progress`, `RubricStore.released` y
`ProfileStore.get` filtran por el `user_id` del que pregunta. Hay pruebas que lo afirman como
propiedad, no como costumbre.

## La cuenta no caduca

Caduca el **código de invitación** (7 días, un solo uso) y la **sesión** (12 horas absolutas).
La cuenta vive hasta que un administrador la desactive: `mrs_users` no tiene columna de
expiración y nada borra filas de usuario.

## Promover de año conserva todo

*Account administration* → **Manage an account** → cambiar *Resident year* → **Save account**.

Los encuentros cuelgan del `user_id`, que no cambia nunca. El año sólo decide qué desafíos se
ofrecen de ahí en adelante. Al promover se invalidan las sesiones activas del residente —un
cambio de privilegios no viaja en una sesión vieja— y los desafíos del año nuevo entran como no
vistos.

Esto es lo que permite el objetivo declarado: que al egresar, después de tres años, el
residente tenga su registro completo bajo la misma cuenta.

## Lo que el residente ve de lo suyo

- **Sus encuentros completados**, con la descarga del Management Trace. Antes del 2026-09-23 su
  trabajo se volvía invisible al terminar: la traza se descargaba durante el encuentro y nunca
  más.
- **Su rúbrica confirmada**, con el puntaje y el documento. Un **borrador nunca** le llega: la
  evaluación es del docente mientras no la complete.
- **El hilo de lo que dijo que haría distinto**, en un solo lugar y junto al encuentro que vino
  después.
- **Su perfil de araña**, con el último encuentro y el promedio, que se actualiza con cada
  rúbrica confirmada.
- **Su expediente completo**, en un archivo. No es un certificado ni una transcripción: es una
  copia de su propio registro, y lo dice dentro.
- **Su contraseña**, que ahora puede cambiar. `change_password` existía desde el principio y no
  llegaba a ninguna pantalla.

## La foto y su acuerdo

La foto es el **primer dato personal identificable** que esta aplicación guarda, así que no
entra en silencio.

- **Nada se guarda sin acuerdo firmado.** `save` se niega si esa persona no aceptó la versión
  vigente. Una versión nueva del acuerdo hay que volver a aceptarla.
- **Se muestra en un solo lugar**: el centro del gráfico de araña, y los documentos que lo
  llevan. La ven el dueño y el docente.
- **El archivo se re-codifica, no se guarda.** Lo que llega se decodifica, se recorta cuadrado,
  se reduce a 256×256 y se escribe como un JPEG nuevo. Nada del original sobrevive, **incluido
  el bloque EXIF**, que en una foto de teléfono lleva de rutina el lugar y el momento. Hay una
  prueba que mete una marca de cámara y una fecha y verifica que desaparecen.
- **Se puede borrar**, en un botón y sin dar razón. El registro del acuerdo se conserva: que
  alguien aceptó, y cuándo, es lo que hace rendible el almacenamiento.

**El texto del acuerdo es un borrador para que el programa lo complete.** Dice lo que el
software hace, que es de lo que puedo responder. Lo que no dice —cuánto tiempo el programa
conserva el registro, dónde está alojada la base, y a quién reclamar— es del programa.

### En el gráfico

La foto va al centro, recortada en círculo, con las iniciales y el año (`NP · R2`). Sin foto,
las iniciales **son** el badge.

Dos cuidados que no son cosméticos:

- El badge se dibuja **debajo** de los contornos, y su radio es el 21% del radio del gráfico,
  dentro del anillo más interno. Un puntaje de 1 nunca queda tapado.
- **Un cero se dibuja en el centro exacto**, encima de la foto, con un anillo del color de la
  página alrededor. Una foto no puede esconder un cero.

## Cómo se elige el próximo desafío

La regla del currículo no cambió: exponer cada desafío una vez, y después volver al mayor vacío
de evidencia del intento más reciente, alternando respecto del anterior.

Lo que se agregó es un **desempate**. Entre los candidatos que esa regla ya estaba eligiendo al
azar, prefiere el que ofrece más **situaciones en las que el residente nunca ha estado**: los
eventos críticos definidos que los casos detrás de ese desafío pueden presentar y que su
historia todavía no incluye.

**Lee cobertura, nunca puntajes.** Un instrumento que eligiera el próximo caso a partir de sus
propias notas estaría dirigiendo al alumno con su propia salida, y esta rúbrica es un piloto
que no otorga nada. "Todavía no observado" es un hecho del currículo; "sacó bajo" es un juicio
sobre una persona. `challenge_targeting` no importa `rubric`, `rubric_store`,
`rubric_progress` ni `progress_store`, y hay una prueba que lo verifica.

**Nunca anula.** La lista que devuelve siempre es un subconjunto de la que el currículo ya
había elegido, y es la lista entera cuando los conteos no discriminan. Sin el desempate, la
asignación es exactamente la de antes. La asignación guardada registra `targeting` para que se
pueda auditar cuál de los dos caminos se tomó.

`curriculum.py` sigue sin saber que la rúbrica existe: el conteo se calcula fuera y se le pasa.
