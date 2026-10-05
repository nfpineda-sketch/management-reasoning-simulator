---
name: ux-antes-despues
description: Cómo comparar un cambio de pantalla del simulador entre ANTES (commit base) y DESPUÉS (candidato). Comprueba que las mismas entradas dejan el mismo registro y estado, revisa el comportamiento en el navegador, toma capturas reales y verifica que no se adelante información, en entornos sintéticos sin red ni credenciales. Usar en encargos de UX o de presentación y para capturas ANTES/DESPUÉS. No autoriza cambios a la app.
---

# UX: ANTES / DESPUÉS

Comparar exige el mismo caso, las mismas entradas y entornos sintéticos aislados. Lo que no pueda controlarse se
declara. Aplica la regla de eficiencia de `CLAUDE.md`: los pasos de navegador y la suite se usan cuando el cambio
lo justifica.

## Parámetros
Los valores son ejemplos, no requisitos:
- base: por ejemplo, el HEAD al iniciar el encargo;
- candidato: un commit o el árbol de trabajo (`TRABAJO`);
- perfil de pasos: por defecto `scripts/perfil_encuentro_clinico.json`, que fija variante, desafío y semilla;
- idioma;
- puertos y directorio de la corrida, siempre fuera del repositorio;
- tamaños: por ejemplo 1440×900, 1366×768 y 1000×768, más un teléfono si el diseño lo contempla.

## Comandos
Los scripts están en `scripts/` de esta skill y no dependen del directorio actual. Cada comando, desde cualquier
directorio del repositorio:

```bash
S="$(git rev-parse --show-toplevel)/.claude/skills/ux-antes-despues/scripts"
python3 "$S/entorno.py" preparar --dir RUN --base <base> --candidato <commit|TRABAJO> --tamanos 1366x768
python3 "$S/entorno.py" iniciar --dir RUN
python3 "$S/equivalencia.py" correr --arbol RUN/antes --salida A.json    # y RUN/despues → B.json
python3 "$S/equivalencia.py" comparar A.json B.json --informe C.json
python3 "$S/capturas.py" --run RUN --salida CAPTURAS
python3 "$S/comportamiento.py" --run RUN --tamano 1366x768
python3 "$S/entorno.py" detener --dir RUN
python3 "$S/entorno.py" limpiar --dir RUN
```

## 1. Entornos aislados
- `entorno.py preparar` copia los dos árboles a un directorio propio de la corrida y crea una base SQLite sintética
  por lado, con cuentas sintéticas separadas por uso (capturas y comportamiento). Nunca datos reales ni la base de
  un despliegue.
- `entorno.py iniciar` levanta un servidor por lado con la revisión de imágenes activa
  (`MRS_IMAGE_REQUIRE_REVIEW=on`, como en el piloto).
- Sin red ni credenciales. Los servidores y `equivalencia.py` corren bajo `scripts/aislamiento.py`:
  - el entorno se arma desde una lista permitida, sin claves, tokens ni proxies;
  - HOME queda dentro de la corrida, sin `secrets.toml`;
  - dentro del proceso se bloquea toda conexión saliente, también a loopback, donde escucha el proxy de salida;
  - una autoprueba confirma el bloqueo al arrancar, y cada intento queda en el log de la corrida;
  - el navegador aborta toda petición que no sea al servidor local.

  `iniciar` se detiene si la autoprueba falla o si el entorno del servidor muestra una variable sospechosa.
  `detener` informa los intentos bloqueados. El entorno y el directorio de cada servidor se leen de `/proc` en
  Linux, y con `sysctl` y `lsof` en macOS.
- Excepción, sólo si es imprescindible: desactivar la revisión de imágenes únicamente en ese entorno temporal
  sintético, con el motivo escrito en el manifiesto de la corrida. Nunca en un despliegue.
- Después de cambiar el CSS o un módulo importado, reiniciar los servidores: Streamlit conserva los módulos entre
  reruns.

## 2. Mismo paciente
- Preferir el mismo asset de paciente en ambos lados, o assets sintéticos aprobados. Con la revisión activa y sin
  aprobaciones en la base sintética, ambos lados muestran la vista neutral.
- `capturas.py` registra la huella de la imagen mostrada. Si difiere entre lados, la comparación visual no está
  totalmente controlada y hay que decirlo; nunca presentarla como idéntica.

## 3. Equivalencia del registro (AppTest)
- `equivalencia.py correr` ejecuta la misma secuencia del perfil en cada árbol. Después de cada paso vuelca los
  eventos, el Management Trace, el estado clínico, lo pendiente y el texto visible; al final, el contenido clínico
  del registro guardado.
- La reproducibilidad usa un mecanismo de prueba acotado y reversible: la semilla del encuentro se fija sólo en la
  vista de `curriculum_runtime`, en `equivalencia.py` y en los servidores de la corrida. Nunca se parchea
  globalmente `secrets` ni otro mecanismo de seguridad; los tokens de sesión siguen siendo aleatorios.
- `equivalencia.py comparar` compara los pasos y el registro, con su contenido clínico y su procedencia.
  - Normaliza sólo rutas técnicas enumeradas, calibradas corriendo dos veces el mismo árbol, e informa cada ruta
    normalizada con su conteo.
  - Nunca excluye campos amplios.
  - Avisa si las dos corridas usaron semillas distintas.
- El resultado esperado es idéntico; cualquier otra diferencia se investiga.

## 4. Nada se adelanta ni se revela
- Que el registro sea igual no basta: hay que comparar lo que la pantalla muestra en cada paso.
- `comparar` marca los hechos clínicos visibles en DESPUÉS que ANTES no mostraba en ese paso (minutos, cifras con
  unidad). Cada uno se revisa a mano.
- Comprobar que no aparecen resultados antes de estar disponibles, hallazgos no obtenidos, oportunidades de
  evaluación, learning focus ni datos ocultos del caso.

## 5. Navegador y capturas
- `comportamiento.py` corre las comprobaciones que declara el perfil: por ejemplo, un solo modo marcado, Enter que
  no envía, el borrador conservado, y un menú que abre y cierra sin mover nada.
- `capturas.py` toma los mismos estados del perfil en cada tamaño y versión, y arma hojas ANTES | DESPUÉS con pares
  de dimensiones iguales.
- Mirar cada captura:
  - recortes, superposiciones, textos partidos y scroll;
  - que las señales clínicas visibles (monitor, avisos, preguntas pendientes) sigan a la vista.
- Si un control cambió de lugar, usar el de cada versión para la misma función y decirlo.

## 6. Perfiles
Los pasos propios de una pantalla viven en un perfil; por ejemplo, el del encuentro clínico incluye la orden
retenida con sus cuatro campos, el ECG, la aclaración y el cierre. No exigir pasos a una pantalla que no los tiene.

## 7. Informar y limpiar
- Informe con el formato de `CLAUDE.md`. Incluir:
  - capturas reales de dimensiones iguales;
  - qué se ve, y dónde se conserva lo que deja de verse;
  - las rutas normalizadas;
  - lo diferido;
  - los límites: navegador sin interfaz, asset controlado o no, barra de Streamlit Cloud distinta.
- `entorno.py detener` y `entorno.py limpiar` actúan sólo sobre los procesos y el directorio que creó esa corrida.
- Esta skill no autoriza cambios a la app ni a sus fixtures. Commit y push se rigen por `verificar-y-entregar` y
  por el encargo.
