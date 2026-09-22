# Borrador para la reunión de research — qué está listo, qué decides tú

> Trabajo de la noche del 2026-09-22, con tu autorización para avanzar y para hasta diez casos
> pagados. Todo lo verificable está verificado y dice cómo se verificó.
>
> - **La sección A es lo que quedó listo para mostrar.** Archivos concretos, en `local-data/`.
> - **La sección B son decisiones tuyas.** No implementé ninguna. La más urgente es B1,
>   porque sin ella no hay app publicada: **no puedo desplegar yo, necesita tu cuenta.**
> - **La sección C son defectos que encontré y arreglé**, con pruebas, sin criterio clínico
>   de por medio. Están en el árbol de trabajo, commiteados sólo si la suite cerró verde.
> - **La sección D es el registro de gasto**, llamada por llamada.

---

## A. Lo que está listo para mostrar

Todo esto existe como archivo y lo puedes abrir ahora mismo. Está en
`local-data/demo_2026-09-22/` (esa carpeta no se versiona: no sale del computador).

| Artefacto | Archivo | Cómo se produjo |
|---|---|---|
| **PDF de Management Trace** (informe del residente, 6 páginas) | `management_trace.pdf` | Una llamada pagada a `gpt-5` sobre el encuentro congelado, validada y renderizada por el código de producción |
| Análisis crudo que lo alimenta | `management_trace_analysis.json` | — |
| **PDF de apoyo docente, versión compacta** (2 páginas de lectura) | `faculty_brief_compact.pdf` | Una llamada pagada a `gpt-5` |
| **PDF de apoyo docente, versión completa** | `faculty_brief_full.pdf` | El mismo informe, sin recortar |
| **Imagen del paciente** | `patient_scene.png` | Una generación `gpt-image-1.5` + una revisión `gpt-5-mini`, aceptada a la primera |
| El encuentro completo del que salen los tres | `session_for_faculty.json`, `management_trace_payload.json` | Caso generado por IA, jugado sin costo por replay |

El caso es el que ya teníamos generado: **`AI-57d0c4847311ae24`**, hombre de 58 años con
disnea progresiva e hipotensión, insuficiencia cardíaca descompensada con shock cardiogénico.
Se jugó una trayectoria correcta de cinco decisiones (estudios sin volumen → VNI y
noradrenalina → dobutamina → furosemida y sonda → UPC), se completó el ciclo entero de
revisión (Decision Review, Expert Comparison, Adaptation Plan) y de ahí salieron los informes.

**Cómo volver a jugar ese caso sin gastar un peso:**

```bash
MRS_OFFLINE_CASES=1 MRS_REPLAY_CASE=local-data/paid_runs/2026-09-22_R1-05_seed20260922_launched/replay_record.json MRS_DEFAULT_CHALLENGE=R1-05 APP_PASSWORD=local .venv/bin/python -m streamlit run app.py --server.port 8503 --server.headless true
```

---

## B. Decisiones tuyas

### B1. Publicar la app — no puedo hacerlo yo

Streamlit Community Cloud despliega desde GitHub con **tu** cuenta. No tengo ni debo tener
acceso. Lo que sí está listo de mi lado:

- La rama `clinical-encounter-v0.13` está 150 commits adelante de `main`, con la suite verde.
- No hay ninguna credencial versionada (`.streamlit/secrets.toml` está en `.gitignore`).
- No hay rutas absolutas en el código versionado.
- Las tipografías que necesitan los PDF (`assets/fonts/LiberationSans-*.ttf`) sí están versionadas.
- `requirements.txt` incluye `reportlab`, `pypdf`, `openai` y `psycopg`.

**Lo que tienes que decidir:**

1. **¿App nueva o repuntar la existente?** Hoy hay una app publicada desde `ai-integration-v0.9.0`.
   Repuntarla a `clinical-encounter-v0.13` es un cambio grande y no puedo probar la versión
   publicada. Mi recomendación: **app nueva**, con su propia URL, y dejar la actual intacta
   hasta que estés conforme. Además está tu regla de no tocar `main` ni `ai-integration-v0.9.0`.
2. **¿Modalidad de acceso?** `APP_PASSWORD` (clave común, lo más simple para una demo) o
   `MRS_AUTH_MODE=accounts` con PostgreSQL. **El PDF de apoyo docente vive en el portal
   docente, y ese portal sólo existe con cuentas.** Si quieres mostrar ese PDF *dentro* de la
   app y no como archivo, necesitas la base de datos. Si basta abrir el PDF que ya tenemos,
   la clave común alcanza.
3. **Versión de Python.** No hay pin en el repo. El código usa `tomllib`, que es 3.11+.
   Streamlit Cloud permite elegirla en la configuración avanzada. Si quieres, agrego el pin.
4. **Los secretos a cargar**, en el panel privado de Secrets: `OPENAI_API_KEY`, `APP_PASSWORD`
   y, si eliges cuentas, `MRS_DATABASE_URL` más el bootstrap del administrador
   (`docs/SETUP_v0.11.0.md` tiene el procedimiento exacto).

> **Ojo con el costo de una app pública.** Sin `MRS_OFFLINE_CASES`, cada persona que entra y
> aprieta *Begin Encounter* dispara una generación pagada más una imagen. Si compartes la URL,
> compartes la tarjeta. Ver B4.

### B2. Qué modelo usa el análisis

Esta es la decisión que más afecta lo que verá tu colega.

| Modelo | Intentos | Pasaron la validación |
|---|---|---|
| `gpt-5-mini` (el configurado hoy) | 2 | **0** |
| `gpt-5` | 2 | 1 |

Las tres fallas fueron distintas y ninguna es un error de código: el modelo escribió un número
en la prosa cuando el diseño reserva las cifras a la evidencia registrada, o citó evidencia
fuera de la ventana permitida. El diseño es correcto; el modelo chico no lo cumple.

Cuando falla, el residente ve *"Your analysis was not available"* con un botón de reintentar.
No hay reintento automático, porque tu regla lo prohíbe.

**Opciones:** (a) cambiar `MRS_TRACE_MODEL` y `MRS_FACULTY_MODEL` a `gpt-5`, que cuesta más por
llamada pero falla menos; (b) dejar `gpt-5-mini` y aceptar que a veces haya que reintentar;
(c) `gpt-5` sólo para el informe docente y `gpt-5-mini` para el del residente.
**Mi recomendación: (a) para la demo**, y medir con calma después. Para la reunión de mañana
los PDF que ya tienes fueron hechos con `gpt-5`.

### B2bis. El generador de casos **no** puede usar `gpt-5`

Lo probé y falla por una razón que no esperaba. La tubería de generación tiene un presupuesto
de tiempo por etapa de **90 segundos**, calibrado con mediciones reales de `gpt-5-mini`
(autor 63 s, correcciones 48 y 54 s, revisión 70 s). `gpt-5` se demoró **119,8 segundos sólo
en la etapa de autoría** y el caso se rechazó con `CASE-CORRECTION-BUDGET` sin llegar a
validarse. Una llamada pagada, 23.605 tokens, sin caso.

O sea: **el modelo del generador y el modelo del análisis son decisiones separadas.** Mi
recomendación es dejar `gpt-5-mini` para generar (es lo que está calibrado y es lo que produjo
el caso que tenemos) y usar `gpt-5` sólo para los dos informes, que son llamadas únicas y sin
presupuesto de tiempo.

Si quisieras generar con `gpt-5`, habría que subir `STAGE_BUDGET_SECONDS`. El costo es de
experiencia: el peor camino pasaría de 4,5 a unos 10 minutos de espera con el residente mirando
la pantalla. No lo toqué; el comentario del código dice explícitamente que el presupuesto y el
peor caso se derivan juntos para que no se separen, y separarlos es decisión tuya.

### B3. Qué debe pasar cuando el análisis no pasa la validación

Hoy: se rechaza el informe completo y no se muestra nada. En el caso que vi, lo único
incorrecto era **una frase** que mencionaba una medida del ecocardiograma.

**Opciones:** (a) dejarlo como está — el rechazo es total y el residente reintenta;
(b) reparar en vez de rechazar, borrando la frase ofensora y dejando el resto;
(c) degradar: mostrar el informe marcando la sección que no cumplió.

No lo toqué porque la regla que se está rompiendo es tuya: *el modelo no puede aportar una
cifra de la ficha*. Cambiar el rechazo por una reparación es cambiar el contrato, no el código.

### B4. Cuánto cuesta un encuentro de verdad

Medido esta noche, no estimado. Con la clave activa y modo no-offline:

| Concepto | Llamadas |
|---|---|
| Generar el caso | 2 a 3 (autor, corrección si falla, revisión) |
| Imagen del paciente | 2 (crear + revisar) |
| **Normalización de lenguaje de cada orden** | **1 por orden enviada** |
| Análisis del Management Trace | 1 |
| Informe docente | 1 |

Un encuentro de diez órdenes son unas **quince a dieciséis llamadas**. La que sorprende es la
normalización: descubrí que costaba una llamada por orden porque una prueba mía las contó
(seis llamadas donde esperaba una).

**Decisión:** ¿la normalización queda activa en la demo? Sin ella el motor sigue entendiendo
español —todo lo que jugamos estas semanas fue con el parser determinista y sin pagar— pero
pierde la tolerancia a redacciones raras. Yo la dejaría **apagada** para la demo y encendida
sólo si quieres mostrarla explícitamente.

### B5. El horizonte de sesenta minutos de los casos generados

Los casos generados declaran su propio horizonte de tiempo. El de la demo trae sesenta
minutos. Los casos del banco corren horas. Consecuencia: en un caso generado no se puede
mostrar una evolución larga, y la trayectoria de cinco decisiones llena el horizonte entero.

**Decisión:** ¿le pedimos al generador un horizonte mínimo mayor (por ejemplo 180 minutos)?
Es un cambio en el contrato de autoría, no en el motor.

### B6. Las magnitudes del eje respiratorio del SCA (viene de ayer)

Quedaron en el commit `2afdd77` marcadas *pending faculty review*. Las dos que más te pueden
chocar: el agotamiento a los ochenta minutos sin ningún soporte, y el peso 0,3 del territorio
inferior.

### B7. La taquicardia por dobutamina sin costo (viene de ayer)

La dobutamina sube la frecuencia a 125 en una isquemia activa y eso no tiene ninguna
consecuencia. Es correcto que suba; la pregunta docente es si debería empeorar algo.

### B8. El idioma (decisión 16, segunda etapa)

El relato del caso, los informes y toda la capa de revisión siguen en inglés. Para una reunión
de research eso puede ser una ventaja o un problema según con quién hables. Los PDF que tienes
están en inglés; las órdenes se escriben en español y se entienden en español.

### B9. Imágenes durante un replay (propuesta mía, no implementada)

Hoy el modo offline retiene la clave en todas partes, que es justamente lo que hace gratis un
replay. Efecto secundario: **un replay no puede mostrar imagen del paciente**. Para la demo
sería ideal poder repetir un caso conocido, gratis, con foto.

Se podría agregar un interruptor explícito y apagado por omisión (`MRS_REPLAY_IMAGES=1`) que
habilite la clave *sólo* para la escena durante un replay. No lo hice porque debilita una
propiedad de seguridad que definiste tú y prefiero que la autorices.

---

## C. Defectos encontrados y arreglados esta noche

Ninguno involucra criterio clínico. Todos salieron de jugar.

### C1. La unidad de paciente crítico no existía

`Hospitalízalo en la unidad de paciente crítico` y `Hospitalízalo en la UPC` se retenían
pidiendo un destino que el residente ya había escrito. Sólo entendía *unidad de cuidados
intensivos*. Ahora entiende UPC y unidad de tratamiento intermedio. `UTI` a secas queda
deliberadamente fuera: en inglés es una infección urinaria.

### C2. El cierre de un caso generado era imposible en su horizonte

Dos reglas se contradecían. El portón de razonamiento **exige** un tiempo de reevaluación
antes de ejecutar cualquier orden; el horizonte **rechazaba** cualquier tiempo una vez que el
reloj lo alcanzaba. El resultado: la disposición final no se podía escribir de ninguna forma y
el encuentro no se podía cerrar.

Una disposición es la entrega del paciente: lo que el residente dice que va a controlar se
controla en la unidad que lo recibe. Ahora el reloj **se detiene** en el horizonte en vez de
rechazar la orden. Seis pruebas.

### C3. El informe del residente se rechazaba por citar su propia respuesta

Este es el importante. Cada decisión guarda una ventana de evidencia: qué había visto el
residente antes de decidir, y qué había visto después. La ventana *posterior* se capturaba
**antes** de que se escribieran los eventos que describen la respuesta, así que era idéntica a
la anterior.

Consecuencia: el modelo, al comparar lo esperado con lo observado, citaba la actualización
clínica que estaba describiendo —lo correcto— y el validador rechazaba el informe entero por
citar evidencia que el residente supuestamente no había visto. **El Management Trace
analizado no podía funcionar nunca en un encuentro real.**

El cursor ahora avanza cuando la respuesta ya está en el registro. Dos pruebas.

---

## D. Registro de gasto

Todo con la clave de `.streamlit/secrets.toml`, que nunca se imprimió ni se guardó en ningún
archivo.

| # | Qué | Modelo | Llamadas | Resultado |
|---|---|---|---|---|
| 1 | Primer intento del informe del residente, con la clave mal acotada | gpt-5-mini | 6 | **Error mío**: dejé pasar la clave a la normalización de cada orden. Cinco llamadas fueron normalizaciones que no quería. El análisis falló |
| 2 | Informe del residente | gpt-5-mini | 1 | Falló: citó evidencia fuera de la ventana (defecto C3) |
| 3 | Informe del residente, ya con C3 arreglado | gpt-5-mini | 1 | Falló: escribió una cifra en la prosa |
| 4 | Informe del residente | gpt-5 | 1 | Falló: una cifra del ecocardiograma en una pregunta |
| 5 | Informe del residente | gpt-5 | 1 | **Aceptado** → `management_trace.pdf` |
| 6 | Informe docente | gpt-5 | 1 | **Aceptado** a la primera → los dos PDF |
| 7 | Imagen del paciente | gpt-image-1.5 + gpt-5-mini | 2 | **Aceptada** a la primera |

El error de la fila 1 fue mío y lo corregí: el guion ahora deja la clave **sólo** para la
llamada de análisis, y el encuentro se juega con el modo offline puesto, que retiene la clave
en todas partes. Las corridas posteriores confirman cero llamadas durante el encuentro.

---

## E. Lo que sigue pendiente de antes

- Brecha banco/generado: morfina (necesita el dolor como observable generado), bloqueo
  neuromuscular e infusión de sedación (necesitan la mecánica del mecanismo `airway`),
  diuresis medida y alta con consecuencia en el motor generado.
- Segunda etapa de la decisión 16 (idioma).
- El PR #1 sigue **sin fusionar**, como pediste.

---

## F. Plan de demostración recomendado

Dos escenarios. El primero no depende de nada que yo no pueda verificar; el segundo necesita
tu decisión B1 y treinta minutos tuyos.

### F1. Demostración local, cero riesgo, cero costo en vivo (lista hoy)

Es la que yo llevaría a la reunión. Nada puede fallar delante del invitado porque nada sale a
internet mientras muestras.

1. **Un caso del banco, jugado en vivo.** Veintiuna variantes, física de verdad, horas de
   evolución, y el español chileno entendido sin pagar una llamada. El tronco coronario de
   ayer es el mejor para mostrar razonamiento: derivadas derechas que descartan el ventrículo
   derecho, morfina que baja el dolor *y* la presión, y un eje respiratorio que ahora se
   mueve con el ventrículo.

   ```bash
   MRS_OFFLINE_CASES=1 MRS_DEFAULT_CHALLENGE=R2-02 APP_PASSWORD=local .venv/bin/python -m streamlit run app.py --server.port 8502 --server.headless true
   ```

2. **El caso generado por IA, por replay.** Mismo motor, caso escrito por un modelo,
   jugable gratis y las veces que quieras (comando en la sección A). Aquí el argumento es que
   la autoría por IA pasa por un validador que la rechaza cuando no es manejable.

3. **Los tres PDF y la imagen**, abiertos desde `local-data/demo_2026-09-22/`. Son el producto
   final: lo que se lleva el residente y lo que lee el docente.

### F2. Demostración publicada (necesita B1)

Si decides publicar, el orden es: crear la app nueva desde `clinical-encounter-v0.13` →
cargar los secretos → **entrar tú primero y hacer un encuentro completo** antes de compartir la
URL. Ese primer encuentro cuesta una generación, una imagen y una llamada por orden, y sirve
para confirmar que la nube se comporta igual que aquí.

Si la app queda pública sin `MRS_OFFLINE_CASES`, considera dejarla arriba sólo durante la
reunión.

---

## G. Cómo revisar lo que hice

```bash
git -C . log --oneline clinical-encounter-v0.13 -8
.venv/bin/python -m pytest -q
.venv/bin/python run_regressions.py
```

Los guiones de las corridas pagadas están en `local-data/paid_runs/`, fuera del repositorio:
`demo_trace_pdf.py` (encuentro + informe del residente), `demo_faculty_pdf.py` (informe
docente), `demo_image.py` (imagen), `generate_one_case.py` (generación). Todos cuentan e
imprimen cada petición que sale de la máquina, y ninguno escribe la clave en ningún lado.
