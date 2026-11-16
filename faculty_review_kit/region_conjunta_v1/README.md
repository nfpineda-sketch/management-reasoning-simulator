# Re-revisión ciega · región conjunta de GI (JOINT_REGION_V1_CANDIDATE)

**Estado: preparado; la re-revisión NO ha empezado.** Nada aquí responde por la persona revisora, ni juzga, ni puntúa.

## Qué es
Tras la primera revisión docente se preparó, sólo para desarrollo, otra configuración conjunta del modelo de hemorragia digestiva. Esa configuración cambia **todas** las trayectorias tratadas, así que se vuelven a juzgar a ciegas **FR-B, FR-C, FR-E y FR-G**. Tus juicios anteriores se conservan aparte y **no** se transfieren.

Casos sintéticos. **No** es validación clínica, ni una configuración calibrada, ni un piloto con residentes. Ninguna configuración es «la esperada».

## Qué revisas y en qué orden
1. **Sólo `CONJUNTO-1`**: los cuatro escenarios de `conjunto_1.md`, en este orden: **FR-B, FR-C, FR-E, FR-G**.
2. **`CONJUNTO-2`** y **`CONJUNTO-3`** (`conjunto_2.md` y `conjunto_3.md`) son vistas de sensibilidad de la misma región. **No los abras** salvo que la docencia los pida después.

Los conjuntos no dicen qué configuración llevan. No hay comparador heredado en esta primera pasada.

## Qué ves en cada escenario
Lo mismo que en la pantalla *Faculty Trajectory Review*: el contexto, qué se hizo y cuándo, la trayectoria de presión (PAS/PAD/PAM) y, como contexto, la frecuencia cardíaca y el relleno capilar. No hay parámetros técnicos.

## Qué contestas
En `formulario_respuestas.md`, por escenario: **Q1 Direction · Q2 Timing · Q3 Magnitude · Q4 Management response · Q5 Educational risk** y el juicio global (**ACCEPT / ACCEPT_WITH_LIMITATION / RECALIBRATE / REJECT**), con las mismas opciones de la pantalla.

## Ciego
- Contesta la primera pasada **antes** de abrir `ABRIR_DESPUES_DE_LA_PRIMERA_PASADA.md` y sin tener delante la revisión anterior.
- El ciego es **de procedimiento**: la pantalla de revisión actual sólo admite el conjunto certificado y fijado por digesto, así que estos candidatos no pasan por ella y nada bloquea el archivo de la clave.

## Límites que conviene saber antes de empezar
- Sólo la presión viene de la configuración candidata. La frecuencia cardíaca y el relleno capilar los calcula el motor vigente del simulador, no la configuración candidata: no cambian con ella y **son iguales en los tres conjuntos**.
- El sangrado sigue activo en todos los minutos de todos los escenarios; no hay control de fuente ni vasopresor.
- La duración de la revisión no se ha medido con una persona.

## Qué no hace este paquete
No elige una configuración, no aprueba ningún parámetro, no cambia lo que ve el residente y no sustituye tu juicio. El registro de tus respuestas es evidencia humana y se guarda aparte del análisis del modelo.
