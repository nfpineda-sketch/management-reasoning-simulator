# Cambios clínicos posteriores a V3 (2026-09-29)

Instrucción docente del 2026-09-29 que cierra las decisiones clínicas analizadas después de V3
(`3d942ee`). V3 conserva sus reglas; cada cambio de abajo tiene su entrada en `corrections_registry.py`,
sus pruebas y la evidencia antes/después medida en el motor real. **Implementado no es validado**: ninguno
de estos cambios tiene todavía revisión clínica externa.

| # | Decisión | Registro | Pruebas |
|---|---|---|---|
| 1 | TEP: D revisada (shock obstructivo, reloj consecutivo, noradrenalina) | C-2026-09-29-10 | `test_pe_obstruction.py`, `test_generated_pe.py`, `test_pe_thrombolysis_screening.py` |
| 2 | DC1: conciencia anclada a la llegada | C-2026-09-29-11 | `test_arrival_consciousness.py`, `test_hypoglycemia_battery.py` |
| 3 | POCUS de la HDA según el llenado efectivo | C-2026-09-29-12 | `test_gi_bleed_pocus.py` |

## 1 · TEP

Detalle, fuentes y trayectorias en `docs/PULMONARY_EMBOLISM_MAGNITUDES.md` (sección «Criterio revisado»).

## 2 · DC1: la conciencia escrita al llegar

Sin tratamiento; «Reassess in 1 minute» tres veces y luego esperas.

| Caso | Llegada | Antes (V3), minuto 1 | Ahora, minutos 1–3 | Ahora, deterioro real |
|---|---|---|---|---|
| `bradycardia_ccb_68m` | Alert, PAS 74 | Drowsy | Alert | Drowsy con PAS 67 (min 25), Obtunded con 64 (min 35) |
| `pulmonary_edema_58m` | Alert, SpO₂ 81 | Drowsy | Alert | Drowsy con SpO₂ 80 (min 15), Obtunded bajo 80 |
| `pulmonary_edema_75f` | Alert, SpO₂ 84 | Drowsy | Alert | Drowsy bajo 82 (min 55) |
| `hypoglycemia_28m` | Drowsy, 34 mg/dL | Obtunded | Drowsy | convulsión en el min 20 como antes; Obtunded bajo 29,5 (min 60) |
| `hypoglycemia_54m_thiamine` | Drowsy, 32 mg/dL | Obtunded | Drowsy | convulsión en el min 20 como antes |

- **Regla.** Al empezar, el encuentro mueve sólo los umbrales que su llegada ya cruzaba, a medio camino entre
  el valor de llegada y el umbral siguiente, que se mantiene: PAS de *Drowsy* 80 → 69,5 en 68m; SpO₂ de
  *Drowsy* 87 → 80,5 en 58m y → 82 en 75f; glucosa de *Obtunded* 45 → 29,5 en 28m y → 28,5 en 54m. Se
  compara antes de redondear. Un nivel peor que el de llegada se deja sólo pasado un margen (PAS 2 mmHg,
  SpO₂ 1 punto, glucosa 1 mg/dL), para que un valor que ronda un umbral no haga parpadear el estado;
  mejorar más allá de la llegada usa el umbral de siempre (alerta con 70 mg/dL, como en 76f).
- **Una glucosa mejor ya no muestra un paciente peor.** Con 5 mL de D50, 28m pasa de 34 a 44 mg/dL: en V3
  quedaba *Obtunded* (peor que al llegar); ahora sigue *Drowsy*.
- **Se conserva:** el deterioro real, la convulsión y el estado postictal, la sedación (morfina 15 mg:
  *Drowsy*), la intubación y la recuperación. Los otros 26 casos del banco no llevan ancla y leen igual; un
  encuentro empezado antes conserva su regla.
- **Batería de hipoglicemia:** T12 pasa en las 12 configuraciones (antes fallaba en 4); ninguna otra
  comprobación cambió. La preservación dorada declara los guiones de 28m y 54m (lectura de llegada y
  estado del ancla); 76f no cambia.

## 3 · POCUS de la HDA

VCI y VI de `gi_bleed_57m` (y `gi_bleed_72f` donde se indica), medidos con el motor real.

| Escenario | Hemodinamia | Antes (V3) | Ahora |
|---|---|---|---|
| Llegada | 88/54 · 124 | 0,9 cm, colapso casi completo · VI pequeño, hiperdinámico, casi obliterado | igual (lo escrito) |
| 1 U de GR | 101/61 · 117 | igual que al llegar (300 mL < 500) | 1,1 cm, >50 % · VI pequeño hiperdinámico **sin obliteración** |
| 2 U de GR | 115/69 · 109 | 1,5 cm, ~50 % · VI **casi obliterado** | 1,5 cm, ~50 % · **cavidad normal con contracción hiperdinámica** |
| 2 U + endoscopía, recuperación en curso | 113/98 → 93 | 1,5 cm · VI casi obliterado | 1,5 cm · cavidad normal con **contracción normal** |
| 1 L de cristaloide, a los 15 min | 91/56 · 122 | **1,5 cm, ~50 %** | 0,9 cm, colapso casi completo (el litro apenas quedó en los vasos) |
| 1 L de cristaloide, una hora después | **80/50** · 128 | **1,5 cm, ~50 %** | **0,7 cm, colapso completo** · obliteración completa |
| Noradrenalina sola | 102/64 · 125 | igual que al llegar | igual que al llegar (el vasopresor no llena) |
| Sin tratamiento 60 min | 80/49 · 129 | igual que al llegar | 0,7 cm, colapso completo |
| 72f, 2 U de GR | 125/77 · 97 | 1,5 cm, ~50 % · «Hyperdynamic contraction» | 2,0 cm, <50 % · cavidad normal con contracción hiperdinámica |
| Intubado | — | diámetro + «respiratory variation not assessable…» | igual, con el diámetro de la escala |

- **Regla.** La VCI y la cavidad del VI leen la circulación de la familia (`f["circulation"]`), que ya integra
  la reposición (sangre 0,36 por unidad; cristaloide 0,00015 por mL), el sangrado que sigue y el cristaloide
  que sale de los vasos (60 % con constante de 30 min). Un vasopresor no la cambia. Escala de vacío a lleno
  (0,7 · 0,9 · 1,1 · 1,5 · 2,0 cm); cada caso entra por su hallazgo escrito y se mueve una posición por cada
  0,30 de circulación ganada o perdida (**parámetro docente**).
- **Cavidad y contracción, separadas.** Llenar reduce y luego termina la obliteración; la contracción sigue
  hiperdinámica hasta que la recuperación que alivia la taquicardia (endoscopía y hemoglobina ≥ 7, alivio
  ≥ 0,5) está en curso.
- **Presión positiva:** se conserva el diámetro y la variación respiratoria se declara no evaluable.
- **Alcance:** sólo la familia `gi_bleed`; neumonía y las demás conservan su regla. Los textos nuevos
  tienen su español (`language.py`).
