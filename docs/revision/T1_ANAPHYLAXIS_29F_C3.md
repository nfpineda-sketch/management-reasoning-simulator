# R-3 · T-1: `anaphylaxis_29f`, C3 YES. Brief para decidir

> **Decidido e implementado el 2026-09-30 (R-3):** C3 queda YES como oportunidad **parcial**: se aceptan como
> evidencia el reconocimiento de la amenaza, la anticipación, pedir ayuda, la preparación y la reevaluación de la
> vía aérea; nunca la ejecución competente ni el cumplimiento completo de C3 (C-2026-09-30-11). TD-47 está
> corregido: con el tubo no se ausculta ni se cobra estridor (C-2026-09-30-10). TDFC no tiene un nivel parcial por
> observación, así que la fila lo dice en su componente, su evidencia y lo que queda fuera: esa es la limitación
> documentada. Lo de abajo queda como el análisis que se presentó.

2026-09-30. Cuando no se indica otra cosa, las fuentes son el código del repositorio y una sonda determinista
del motor, sin proveedor:

- 29f, estado de llegada;
- 6 minutos con cada conducta.

## 1. Qué significa C3

C3 es la EPA de medicina de urgencia del Royal College (EPA Guide 2018, p. 20; meta de 20 observaciones)
**«Manage airway and ventilation»**. Tal como el repositorio la recoge (`objectives.py`, `tdfc_declarations.OUTSIDE`),
comprende:

- valorar y preparar la vía aérea;
- decidir oxígeno y soporte ventilatorio;
- intubar en una vía aérea normal o difícil anticipada;
- el manejo posterior a la intubación y el ventilador;
- la ventilación manual y la laringoscopía;
- reevaluar.

**El simulador observa sólo el razonamiento:** «Reason about available simulated oxygen, airway preparation, and
ventilation support and reassess the response». Declara que no evalúa laringoscopía, colocación del tubo,
ventilación manual ni otras destrezas manuales.

## 2. Qué componente de C3 se pretende observar aquí

La fila TDFC aprobada (TDFC-REVIEW-1) declara:

- **Componente:** «Anticipating a difficult airway, giving oxygen and reassessing the airway after epinephrine».
- **Evidencia esperada:**
  - nombra el estridor como amenaza;
  - pide oxígeno;
  - prepara la vía aérea o pide ayuda;
  - reevalúa el estridor después de la dosis.

## 3. Qué información recibe el residente

- **Presentación:** exantema que se extiende, cara hinchada, respiración ruidosa, ansiosa, habla en frases cortas.
- **Signos vitales:** PA 84/46, FC 126, SpO2 91 %, FR 28, trabajo respiratorio aumentado.
- **Examen:**
  - sibilancias espiratorias difusas y **estridor inspiratorio audible**;
  - edema periorbitario y **de labios**;
  - despierta y orientada, con respuestas cortas por la respiración.
- **Lo que el caso no describe:**
  - ronquera o cambio de voz, babeo, ni edema de lengua o úvula;
  - ninguna valoración de la dificultad de la vía aérea (anatomía, apertura bucal, cuello).

## 4. Qué puede hacer sobre la vía aérea y la ventilación

| Acción | ¿Se ejecuta? | Efecto en el motor |
|---|---|---|
| Oxígeno (dispositivo y flujo) | Sí | Sube la SpO2 |
| «Prepare for intubation» | Sí | Sólo queda registrado («Airway equipment prepared; intubation has not occurred»); **ningún efecto fisiológico** |
| Pedir ayuda (interconsulta) | Sí | Queda registrada |
| Bolsa-mascarilla | Sí | FiO2 0,85 |
| VMNI | Sí, en general | Ninguna regla propia de la obstrucción alta |
| Intubación (exige modo, FiO2 y PEEP) | Sí | **Siempre resulta**, en 5 minutos, sin dificultad, falla ni «no intubar, no oxigenar» |
| Vía aérea quirúrgica | No | No es una acción del motor |
| Adrenalina nebulizada como tratamiento de la vía alta | No | «An upper airway that is closing is not relieved by a nebulizer» |
| Adrenalina IM o IV | Sí | Es lo único que resuelve la reacción, y con ella el estridor |

## 5. Qué consecuencias fisiológicas modela el motor

- **El estridor es binario:** aparece cuando la reacción es de 0,80 o más. Resta 6 puntos de SpO2 y lleva el
  esfuerzo a 1,5 o más. El broncoespasmo se modela aparte.
- **La reacción sin tratar progresa** (0,030 por minuto) hacia la hipotensión y el paro, en unos 25 minutos.
- **Lo que mostró la sonda a los 6 minutos:**

| Conducta | SpO2 | PAS | Estridor |
|---|---|---|---|
| Sólo oxígeno a 15 L/min | **99 %** | 77 | Persiste; la reacción sube a 1,21 |
| Oxígeno más «Prepare for intubation» | 99 % | 74 | Persiste; la trayectoria no cambia |
| Oxígeno más intubación | 99 % | 71 | **El estridor sigue marcado después de intubar**; esfuerzo «Ventilator dyssynchrony» sin sedación |
| Adrenalina IM 0,5 mg al aire ambiente | 86 % | 91 | La reacción baja a 0,84 y va resolviéndose |

- **Lo que no se modela:** obstrucción completa, progresión del edema de la vía aérea con independencia de la
  reacción, intubación difícil o fallida, y cualquier consecuencia de preparar la vía aérea tarde o no
  prepararla.

## 6. ¿Se puede observar un manejo de la vía aérea suficientemente rico?

**No del todo.** Las decisiones sobre la vía aérea no tienen consecuencias en el motor:

- preparar o no preparar da la misma evolución;
- intubar siempre resulta;
- el oxígeno solo corrige por completo la caída de SpO2 del estridor. Eso es realista, porque la SpO2 es un signo
  tardío de la obstrucción alta, pero deja sin consecuencia la decisión sobre la vía aérea.

La evolución depende de la adrenalina.

## 7. ¿O sólo se observa el reconocimiento?

Se observa sobre todo esto:

- el reconocimiento de la amenaza de la vía aérea dentro de la anafilaxia;
- la adrenalina y el oxígeno;
- la reevaluación.

Lo propio de C3, anticipar una vía aérea difícil, se ve sólo como **intención registrada**: nombrar la amenaza,
preparar, pedir ayuda y reevaluar. No se ve como manejo de sus consecuencias.

## 8. Clasificación

**PARTIAL.**

- **Es una oportunidad real**, porque la amenaza está presente y la anticipación se registra y se puede juzgar.
- **No es directa**, porque el manejo de la vía aérea y de la ventilación no cambia nada y la intubación no se
  pone a prueba.
- **Límite del sistema:** TDFC hoy sólo distingue YES y NO. La categoría parcial existe para los vínculos entre
  marcos (DF-14), no para las oportunidades.

## 9. Qué queda fuera del encuentro

- La técnica: laringoscopía, tubo, bolsa-mascarilla y vía aérea quirúrgica.
- Los algoritmos de vía aérea difícil ejecutados de verdad.
- El manejo posterior a la intubación y el ventilador; en el banco sólo se ajusta en el asma.
- La obstrucción completa y la intubación fallida.
- Pediatría y el contexto clínico real.

## 10. Recomendación: **OTHER, YES acotado**

**Mantener C3 YES para el piloto sólo como oportunidad parcial y acotada:**

1. **Componente:** reconocer la amenaza de la vía aérea alta y anticipar una vía aérea difícil, lo que incluye
   adrenalina primero, oxígeno, pedir ayuda capaz de manejar la vía aérea o prepararla (también la quirúrgica), y
   reevaluar el estridor después de la dosis.
2. **Regla de confirmación:** el docente confirma C3 sólo si esa anticipación propia de la vía aérea aparece.
   Nunca por la adrenalina y el oxígeno solos.
3. **Registrar como deuda** que el estridor sigue después de intubar (TD-47) y que las decisiones sobre la vía
   aérea no tienen consecuencia.

**Si su estándar para C3 exige un manejo de la vía aérea con consecuencias**, lo coherente es **CHANGE TO NO**.

Cualquiera de las dos cambiaría una declaración TDFC. Se implementa después, con su aprobación, sólo en
encuentros nuevos. T-2, T-3 y T-4 siguen como están mientras tanto.
