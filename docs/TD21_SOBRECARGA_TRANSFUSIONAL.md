# TD-21 · Sobrecarga transfusional durante una hemorragia activa

Ciclo 7 · 2026-09-28 · decisión docente: **principio D** (no la opción A).
Registro: C-2026-09-28-12. Pruebas: `test_transfusion_overload.py`.

## El problema

- **La regla anterior.** La sobrecarga transfusional se disparaba cuando la
  hemoglobina, antes de la unidad, era ≥ 10 g/dL
  (`TRANSFUSION["unnecessary_above_g_dl"]`).
- **Por qué fallaba en trauma.** La familia trauma no baja la hemoglobina con la
  pérdida. Transfundir un shock hemorrágico, lo correcto, disparaba la
  sobrecarga: «the haemoglobin was already adequate». Evidencia en
  `AUDITORIA_DF23_CICLO6.md` §7.1.

## A frente a D

| Criterio | A · unidades que exceden la pérdida modelada | **D · suspender la regla de Hb mientras la hemorragia modelada siga activa** |
|---|---|---|
| Plausibilidad clínica | Crea una equivalencia «mL perdidos → unidades permitidas»: una seudofórmula difícil de defender | Durante una hemorragia activa, una Hb aislada no dice si sobra volumen. Es el razonamiento clínico |
| Complejidad | Contabilidad por unidad contra el déficit | Un predicado (`trauma_hemorrhage.active`) y una condición en la regla, unas 25 líneas |
| Consecuencias no buscadas | Cuenta como sobrecarga, por aritmética, la sangre dada mientras se sangra | La sobretransfusión mientras la fuente sigue abierta ya no da sobrecarga. Es lo que dice el principio aprobado |
| Reversibilidad | Sí | Sí: `HAEMORRHAGE_SUSPENDS_THE_HAEMOGLOBIN_RULE = False` vuelve a la Hb sola |
| Verificabilidad | Sí | Sí: sondas deterministas y 4 pruebas nuevas |

**Se implementó D:** es pequeña, general dentro de su clase y robusta. No hizo
falta reconstruir el modelo hemorrágico.

## La regla implementada

- **Hemorragia activa (trauma):** una fuente que sigue sangrando o sangre
  perdida todavía no repuesta. Antes del primer minuto, el déficit de llegada
  cuenta como ya perdido.
  - **Sin umbral numérico nuevo:** lo que hace significativa la hemorragia son
    las fuentes que declara el caso.
- **Mientras dure,** las unidades no se cuentan como innecesarias por la Hb.
- **Cuando el sangrado está controlado y la pérdida repuesta,** la regla
  genérica vuelve a aplicarse.
- **La HDA no cambia (interpretación del AI Advisor).**
  - Allí la Hb del modelo baja con el sangrado y se diluye con cristaloide: no
    está aislada de la pérdida.
  - Una Hb ≥ 10 ya dice que la pérdida se repuso. Rige la regla docente del
    2026-09-20: «the threshold is the haemoglobin, not the diagnosis».
  - Si el docente quiere D también en la HDA, es una línea (decisión en la
    cola).
- **No hay otra evidencia de sobretransfusión modelada.** Fuera de la regla de
  Hb no se agregó ninguna.
- **Sin cambios en:** el −3, los eventos críticos y las rúbricas. Ninguno lee
  la sobrecarga.
- **Casos generados de sangrado:** no aplica. Corren en otro motor, que no
  tiene la regla de sobrecarga.

## ANTES / DESPUÉS (sondas deterministas, sin red)

| Escenario | ANTES | DESPUÉS |
|---|---|---|
| T1 · `trauma_limb_hemorrhage_27m`: torniquete y 2 U en 20 min (apropiado) | Sobrecarga 2,0 U. SpO₂ 97 → 89, FR 34, crepitantes | **Sin sobrecarga.** SpO₂ 97, FR 26 |
| T2 · `trauma_hemothorax_41m`: 2 U desde la llegada, sangrando (apropiado) | Sobrecarga 1,2 U. SpO₂ 86 | **Sin sobrecarga.** SpO₂ 91; sigue en shock por el sangrado, como corresponde |
| T3 · 27m: controlado y repuesto (2 U + 1 L), luego 8 U más (excesivo) | Sobrecarga 4,0 U | **Sobrecarga 4,0 U** (el mecanismo sigue) |
| G1 · `gi_bleed_57m`: 2 U (apropiado) | Sin sobrecarga | Sin sobrecarga |
| G2 · `gi_bleed_72f`: 2 U (apropiado) | Sin sobrecarga | Sin sobrecarga |
| G3 · 57m: 8 U antes de la endoscopía (Hb 12,4) | Sobrecarga 3,3 U | Igual |
| G4 · 57m: endoscopía y 8 U más | Sobrecarga 4,0 U | Igual |
| N1 · `pneumonia_46f`: 2 U sin anemia | Sobrecarga 2,0 U | Igual |
| N2 · `anaphylaxis_29f`: 2 U sin anemia | Sobrecarga 2,0 U | Igual |

**Consistencia con el POCUS.** El REVIEW de `AUDITORIA_DF23_CICLO6.md` §5 queda
resuelto: el POCUS repetido del caso de extremidad («No B-lines») ya no
contradice una sobrecarga, porque ya no hay una sobrecarga falsa.
