# 05 · Escenarios de la primera revisión

**Cinco escenarios núcleo y uno opcional**, en este orden. Duración estimada del conjunto núcleo: ≈ 32 minutos de escenarios + 5 de orientación + 3 de resumen ≈ **40 minutos** (estimación, **no medida con una persona**). El selector `Review encounter` de la pantalla lista siete escenarios; **sólo corre los de esta lista**.

| Orden | Escenario | Caso | Min. | Por qué está | Pregunta principal |
|---|---|---|---|---|---|
| 1 | **FR-B** · Hombre de 57 años · tratamiento precoz | `gi_bleed_57m` | 8 | Es el escenario más simple y sirve para familiarizarte con la pantalla. Cubre el tratamiento temprano y eficaz y la reposición de volumen con sangre (vía, 1 litro de suero fisiológico, 2 unidades de glóbulos rojos). | Con un tratamiento precoz y completo, ¿la presión empieza a responder en el momento adecuado y con un tamaño plausible? |
| 2 | **FR-A** · Hombre de 57 años · deterioro sin tratamiento | `gi_bleed_57m` | 6 | Muestra la dirección y el ritmo del deterioro sin tratamiento y es la revisión principal de la parada por límite de colapso: el experimento se detiene antes del estado del paciente que la autoridad de presión no sabe representar. | Sin tratamiento, ¿la presión se deteriora en una dirección coherente y a un ritmo aceptable, y la parada ocurre en un punto comprensible? |
| 3 | **FR-E** · Mujer de 72 años · tratamiento tardío y recuperación | `gi_bleed_72f` | 7 | Cubre el tratamiento tardío y la recuperación posterior: dos horas sin tratar y luego vía, 1 litro y 2 unidades. Segundo caso (otra edad y sexo), lo que ayuda a distinguir un problema del caso de uno general. Incluye la comparación de consciencia en un curso reversible. | Tras dos horas sin tratamiento, ¿el deterioro y la recuperación (momento, velocidad y tamaño) son plausibles? |
| 4 | **FR-G** · Mujer de 72 años · infusión larga (sólo suero) | `gi_bleed_72f` | 6 | Es el único escenario de tratamiento parcial (suero sin sangre) y el más sensible al tiempo: un litro en 60 minutos mientras el sangrado continúa. | Con sólo suero y una infusión larga, ¿la trayectoria de la presión durante y después de la infusión es plausible? |
| 5 | **FR-F** · Hombre de 57 años · una acción que el experimento no puede juzgar | `gi_bleed_57m` | 5 | Cubre la parada operativa (no clínica): se ordena un vasopresor que la autoridad de presión no representa. Evalúa si la parada se entiende y si confunde. Aporta poca información de presión: se incluye por la experiencia de la parada. | ¿La parada por una acción que el experimento no puede juzgar es comprensible, está libre de lenguaje clínico o terminal y no confunde a quien aprende? |
| 6 (opcional) | **FR-D** · Mujer de 72 años · deterioro sin tratamiento (OPCIONAL) | `gi_bleed_72f` | 5 | Reserva. Sólo si FR-A te deja una duda de dirección o de ritmo (separa «problema del caso» de «problema general») o si te sobra tiempo. Es el único deterioro sin tratamiento del segundo caso. | Lo mismo que en FR-A, para el segundo caso: dirección, ritmo y comprensibilidad de la parada. |

## Cobertura
| Lo que queríamos cubrir | Escenario(s) | Nota |
|---|---|---|
| Deterioro sin tratamiento | FR-A (y FR-D, opcional) | |
| Tratamiento temprano eficaz | FR-B | |
| Tratamiento tardío | FR-E | FR-C se excluyó por redundancia |
| Tratamiento parcial (sólo suero) | FR-G | |
| Sangre / reposición definitiva de volumen | FR-B y FR-E (2 unidades de glóbulos rojos) | No existe entre los siete guiones uno sólo de sangre ni uno de control definitivo de la fuente: la reposición con sangre es lo más cercano |
| Parada efectiva | FR-A (límite de colapso) y FR-F (acción que el experimento no puede juzgar) | |
| Infusión larga o sensible al tiempo | FR-G | |

## Excluidos
- **FR-C** · Hombre de 57 años · tratamiento tardío. Excluido por redundancia: hace la misma pregunta que FR-E (tratamiento tardío y recuperación). FR-E es más informativo: segundo caso, seguimiento más largo, recuperación que supera la presión de llegada y comparación de consciencia reversible.

## Qué te damos de cada escenario
- `paquetes/FR-x_hoja_autoridad.md`: lo que ves **antes** de revelar (presentación, guion, trayectoria de la presión de la autoridad, manejo, parada).
- `paquetes/FR-x_hoja_comparador.md`: lo que ves **después** de revelar (comparación con el modelo heredado y comparación de consciencia). **No se abre antes.**
