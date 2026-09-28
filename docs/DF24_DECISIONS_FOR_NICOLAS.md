# DF-24 · Decisiones para Nicolás

Ciclo 6 · 2026-09-28 · rama `clinical-encounter-v0.13`.

**Qué es.** Las siete decisiones de DF-24 que siguen pendientes. Cada una se
responde en una línea; la plantilla está al final.

- **Ya decidido e implementado en este ciclo, no se pregunta de nuevo.**
  L-F01 (los temas de historia se leen de la copia congelada del caso; un
  encuentro sin copia queda «no disponible», nunca con el banco de hoy) y L-F04
  (la trayectoria se ordena por fecha y hora del encuentro; la hora de
  confirmación queda como dato de auditoría). L-F04 **no** cambió qué revisión
  de un mismo encuentro cuenta: eso es L-F02, abajo, y sigue pendiente.
- **Nada de lo que sigue se implementó.** Cada comportamiento se verificó en el
  código el 2026-09-28 (archivo:línea). Otra sesión edita algunos de estos
  archivos: las líneas son las de esta lectura.
- **Fuentes:** `docs/AUDITORIA_NOCTURNA_CICLO5.md` (secciones 1 y 2) y DF-24 en
  `docs/COLA_DECISIONES_AI_ADVISOR.md`.

**Cinco palabras técnicas, en breve:**

- **Revisión:** cada vez que se guarda la rúbrica de un encuentro nace una
  versión numerada (1, 2, 3…). Nada se sobrescribe.
- **Radar:** el gráfico de araña D1–D5 del perfil.
- **Exportación:** el archivo JSON que la persona residente descarga con su
  registro completo.
- **Transición:** la regla provisoria por la que TD1, F1, C1, C3, C4 y C14 se
  pueden valorar en todo encuentro mientras nadie haya revisado el caso.
- **Sandbox:** el modo de prueba docente. Sus encuentros no se pueden valorar.

## Resumen

| Ítem | El problema en una frase | Qué toca | Recomendación |
|---|---|---|---|
| I-F02 | La exportación no dice quién confirmó la rúbrica | Sólo exportación | A |
| L-F02 | Con un reloj desfasado, el radar usa una revisión ya superada | **Radar** | A |
| I-F18 | Al abrir una base antigua, la «foto» de una confirmación absorbe observaciones posteriores | Confirmación de objetivos | B |
| L-F07 | C14 sigue valorable donde nadie lo revisó | Oportunidades | B (y D más adelante) |
| Observación anulada | La persona residente ve el juicio anulado, las notas y el motivo | Pantalla | A |
| Retiro de una rúbrica confirmada | Hoy no se puede retirar | Pantalla (A) · **radar y eventos críticos** (B) | A ahora |
| Meta cambiada tras confirmar | «3/5 · Confirmed», sin explicación | Pantalla | A |

**Requieren su aprobación explícita,** porque el puntaje y el radar están
congelados: L-F02 y, si la elige, la opción B del retiro. Los demás tocan sólo
exportación, metadatos, oportunidades o pantallas: ningún puntaje, radar ni
evento crítico.

---

## 1 · I-F02 · La exportación no dice quién confirmó la rúbrica

**Problema.** En el archivo que la persona residente descarga, cada rúbrica
confirmada trae `reviewed_by` vacío.

**Comportamiento actual (verificado).**

- `RubricStore.progress()` lee las rúbricas confirmadas sin unir la tabla de
  cuentas, así que no trae quién revisó (`rubric_store.py:417-432`).
- La exportación copia ese dato inexistente:
  `"reviewed_by": review.get("reviewer", "")` (`resident_portal.py:273`).
- El PDF de la misma rúbrica sí lo muestra («Reviewed by»), porque lo lee por
  otra vía (`rubric_store.py:376-389`; `rubric_presentation.py:264-265`).

**Por qué importa.** Dos copias del mismo registro, ambas de la persona
residente, dicen cosas distintas. Un campo vacío se lee como «nadie».

**Ejemplo mínimo.** Docente A confirma la rúbrica del encuentro E2 de R1. El
PDF de E2 dice «Reviewed by: docente_a». La exportación de R1 dice
`"reviewed_by": ""`.

**Opciones.**

- **A.** Traer a la exportación el nombre de cuenta de quien confirmó, el mismo
  que ya muestra el PDF.
- **B.** Quitar el campo de la exportación, si prefiere no exportar ese nombre.
  El PDF lo seguiría mostrando.
- **C.** Dejarlo vacío, como hoy.

**Recomendación.** A.

**Riesgo.** Mínimo: el nombre ya viaja en el PDF. La función que se toca
también alimenta el radar, pero sólo se le agrega un dato; una prueba debe
mostrar que ningún número cambia.

**Esfuerzo.** Una sesión corta con 2 pruebas: la exportación trae quién revisó,
y el radar no cambia. La consulta es la que L-F04 ya tocó en este ciclo.

---

## 2 · L-F02 · Con un reloj desfasado, el radar usa una revisión ya superada

**Problema.** Si un encuentro tiene dos rúbricas confirmadas (la segunda
corrige a la primera), el perfil elige la «última» por hora. El resto de la
aplicación la elige por número de revisión.

**Comportamiento actual (verificado).**

- La hora la pone el reloj del servidor de la aplicación, en segundos
  (`rubric_store.py:342`).
- El perfil y el radar ordenan por hora y se quedan con la última de cada
  encuentro (`rubric_store.py:417-434`).
- El PDF de la persona residente toma la de número mayor
  (`rubric_store.py:376-381`), y la pantalla docente también
  (`rubric_store.py:441-445`; `rubric_portal.py:92-93`).

**Por qué importa.** El mismo encuentro muestra dos puntajes según la pantalla,
y el radar se dibuja con la revisión superada. Sólo pasa si un reloj se atrasa
(dos servidores, un ajuste de hora). Con relojes normales, ambas reglas
coinciden.

**Ejemplo mínimo.** E2 de R1. La revisión 1 se confirma a las 10:00:00 con
D1 = 3. Docente B la corrige: la revisión 2 se confirma a las 10:00:05 con
D1 = 1, pero desde un servidor 10 s atrasado queda registrada a las 09:59:55.
Radar de R1: D1 = 3. PDF de E2 y pantalla docente: D1 = 1.

**Opciones.**

- **A.** Elegir por número de revisión, como el resto de la aplicación. La hora
  queda como dato de auditoría.
- **B.** Mantener la hora y dejarlo documentado.
- **C.** A, y además que la hora la ponga la base de datos y no el servidor.
  Evita el desfase en adelante, pero es un cambio más amplio.

**Recomendación.** A.

**Riesgo.** Toca qué revisión alimenta el radar: requiere su aprobación
explícita. Con relojes normales no cambia ningún resultado, y una prueba lo
demuestra.

**Esfuerzo.** Una sesión corta con 2 pruebas: reloj atrasado, y dos
confirmaciones en el mismo segundo. L-F04 ya cambió esta misma consulta (orden
entre encuentros) y dejó intacta, a propósito, la elección dentro de cada
encuentro: L-F02 sería una línea en la misma función.

---

## 3 · I-F18 · Al abrir una base antigua, la «foto» de una confirmación absorbe observaciones posteriores

**Problema.** Hoy, al confirmar un objetivo, se guarda una «foto»: la lista de
observaciones que sostienen esa confirmación. Las confirmaciones guardadas
antes de que existiera la foto no la tienen. Cuando una base así se abre con el
código actual, se les arma una con todas las observaciones vigentes, también
las registradas después de confirmar.

**Comportamiento actual (verificado).**

- La foto de una confirmación antigua toma todas las observaciones no anuladas,
  sin mirar su fecha (`progress_store.py:162-167` y `234-237`).
- La foto decide dos cosas:
  - qué observaciones son «posteriores a la confirmación», que encienden
    «Review later concerns» si alguna es insuficiente
    (`progress_store.py:317-319` y `342`);
  - si anular una observación reabre la confirmación
    (`progress_store.py:655-661`).

**Por qué importa.** Contradice la regla escrita
(`docs/LONGITUDINAL_PROGRESS.md`): una preocupación posterior se marca para
revisión, y anular una observación posterior no cambia la decisión anterior.
Sólo afecta a bases creadas antes de la foto.

**Ejemplo mínimo.** Base antigua. R1 tiene R1-04 confirmado el 1 de
septiembre con O1, O2 y O3 (meta 3). El 5, docente B registra O4, «Needs
improvement». El 10 se abre la base con el código actual y la foto toma
O1–O4. Resultado:

- no aparece «Review later concerns», y debería;
- si alguien anula O4, la confirmación se reabre, y no debería.

**Opciones.**

- **A.** La foto de una confirmación antigua toma sólo las observaciones
  registradas hasta la hora de esa confirmación. La prueba debe insertar filas
  de verdad; la prueba de migración actual no inserta ninguna (I-F17).
- **B.** A, más una consulta de sólo lectura a la base del despliegue para
  saber si alguna foto ya se armó así. Necesita su autorización.
- **C.** Dejarlo como está.

**Recomendación.** B.

**Riesgo.** Si la base del despliegue ya pasó por esa conversión, sus fotos ya
están escritas y A no las rehace: B dice si hace falta hacer algo. La hora de
la confirmación es la de su último cambio, la mejor referencia disponible.

**Esfuerzo.** Una sesión corta con 2 pruebas. La consulta, unos minutos.

---

## 4 · L-F07 · C14 sigue valorable donde nadie lo revisó

**Problema.** La transición de C14 se retiró sólo en los 30 casos del banco ya
revisados. Donde no hay declaración, C14 sigue valorable:

- en los casos generados por IA;
- en los encuentros PS001, el único escenario de R1-03, R1-04 y R2-01;
- en las 9 composiciones del catálogo de hipoglicemia, aunque los 3 casos del
  banco de los que derivan dicen C14 NO.

**Comportamiento actual (verificado; la resolución se ejecutó en memoria).**

- Sin declaración, C14 queda «not reviewed · valorable · transición»
  (`observation_opportunities.py:70` y `189-191`).
  - Así sale para un caso generado, para un encuentro sin caso autorado (como
    PS001) y para `hypoglycemia_cfg_insulin_failed_severe`.
  - `hypoglycemia_28m`, en cambio, da «no · no valorable · declarado».
- Las declaraciones C14 se escriben sólo en los casos del banco, no en las
  composiciones (`case_assessment_bank.py:435-436` y `1688-1689`).
- Hoy las composiciones sólo se juegan en el sandbox docente
  (`hypoglycemia_catalog.py:630-632`), y un encuentro sandbox no se puede
  valorar (`progress_store.py:469-471`). Para ellas, el problema es latente.

**Por qué importa.** La cola docente ofrece C14 en encuentros donde nadie
decidió si el POCUS guía una decisión. En las composiciones, además, se
contradice el NO de su caso de origen el día en que una pase al banco.

**Ejemplo mínimo.** R1 juega R2-01 (escenario PS001) y la cola lista C14 como
valorable. `hypoglycemia_28m` dice C14 NO. Su composición
`hypoglycemia_cfg_insulin_failed_severe`, el mismo caso con la vía fallida,
queda abierta.

**Opciones.**

- **A.** Dejarlo todo como está.
- **B.** Mantener la transición en los generados y en PS001, que no tienen
  declaraciones (DF-12). Declarar C14 NO en las 9 composiciones, con el NO de
  su caso de origen y la firma de su revisión.
- **C.** Cerrar C14 en todo lo no declarado: sólo contaría lo revisado.
  Adelanta el retiro de la transición y le quitaría C14 a PS001, cuyo POCUS sí
  cambia con la contractilidad (`regression_v085_dynamic_ps001_pocus.py`).
- **D.** Revisar PS001 como un caso más (C14 y TD/F/C): es la única fuente de
  tres desafíos.

**Recomendación.** B ahora. D cuando se revisen las oportunidades TD/F/C.

**Riesgo.**

- B no cambia nada que hoy se valore, porque las composiciones son de sandbox.
- C podría quitar oportunidades reales.
- A deja la contradicción para el día en que una composición pase al banco.

**Esfuerzo.**

- B: una sesión corta, con 9 declaraciones con procedencia y 1 prueba. Si se
  registra como corrección, hay que regenerar el catálogo publicado de
  hipoglicemia.
- D: una revisión clínica como la de C14.

---

## 5 · Observación anulada: qué ve la persona residente

**Problema.** Anular una observación la saca de la cuenta y la conserva en el
historial. Falta decidir qué ve la persona residente.

**Comportamiento actual (verificado).**

- Ve la misma tabla y el mismo historial que la docencia
  (`progress_portal.py:397-399`):
  - la fila con el juicio original («Satisfactory: Yes» o «No») y el estado
    «Voided» (`progress_portal.py:62-73`);
  - las notas de retroalimentación, el aviso «This observation was voided and
    contributes no credit.» y el motivo escrito (`progress_portal.py:92-97`).
- Si la observación sostenía una confirmación, la confirmación se reabre con el
  motivo «Assessment voided: …», y también lo ve (`progress_store.py:655-661`;
  `progress_portal.py:101-104`).
- El formulario de anulación no avisa que la persona residente leerá el motivo
  (`progress_portal.py:364-378`).

**Por qué importa.** Transparencia, frente a tono y privacidad. Un motivo
escrito sin pensar en quien lo lee llega igual, por ejemplo «se confundió con
el encuentro de otra persona residente».

**Ejemplo mínimo.** Docente A registra C14 «Satisfactory» para R1 en E3, y
luego lo anula con el motivo «cité evidencia de otro encuentro». R1 ve:

- «Satisfactory: Yes · Voided»;
- las notas;
- el aviso;
- el motivo.

**Opciones.**

- **A.** Mantener lo que ve, y avisar en el formulario de anulación que la
  persona residente leerá el motivo.
- **B.** Mostrar la fila como anulada, sin el motivo.
- **C.** Ocultarle las filas anuladas. La docencia y la auditoría las
  conservan.

**Recomendación.** A.

**Riesgo.**

- Con A, un motivo mal escrito sigue llegando, pero quien lo escribe lo sabe.
- Con B o C, la persona residente ve cambiar su cuenta sin explicación. Con B
  o C conviene, además, dejar de enviar esos datos a su sesión (I-F25).

**Esfuerzo.** A: una línea de texto y 1 prueba. B o C: una sesión corta con 2
pruebas.

---

## 6 · Retiro de una rúbrica confirmada

**Problema.** Una rúbrica confirmada no se puede retirar. Sólo hay dos
estados: borrador y confirmada.

**Comportamiento actual (verificado).**

- Los estados posibles son `draft` y `confirmed` (`rubric_store.py:31`;
  restricción de la tabla en `rubric_store.py:209`).
- La pantalla docente muestra la revisión más nueva, sea borrador o no
  (`rubric_portal.py:92-93`).
- La persona residente y el perfil ven la última confirmada
  (`rubric_store.py:376-381` y `417-420`).
- Por eso un borrador posterior no retira nada: la docencia ve el borrador, y
  la persona residente sigue viendo la confirmada.

**Por qué importa.** Una rúbrica confirmada por error (encuentro o persona
equivocada) deja el encuentro en el radar y su evento crítico en la cuenta.
Sólo se puede confirmar otra revisión con otros puntajes.

**Ejemplo mínimo.** Docente A confirma la rúbrica de E2 de R1 con D1 = 1 y un
evento crítico (−3). Descubre que evaluó el encuentro equivocado y abre un
borrador para corregir. Su pantalla muestra el borrador. R1 y el radar siguen
con la confirmada, y el evento sigue contado.

**Opciones.**

- **A.** Mantenerlo y avisar en la pantalla docente: «este borrador no
  reemplaza la revisión confirmada que ve la persona residente».
- **B.** Agregar un estado «retirada», que sólo se agrega y nunca borra. Con
  motivo y firma, saca el encuentro de:
  - el perfil y el radar;
  - el documento de la persona residente;
  - la cuenta de eventos críticos.
- **C.** Que un borrador posterior despublique la confirmada. No se recomienda:
  cada edición en curso le quitaría a la persona residente una evaluación ya
  confirmada.

**Recomendación.** A ahora. B cuando aparezca un caso real que lo pida.

**Riesgo.**

- Con A, un error de confirmación sólo se corrige confirmando otra revisión.
- B toca el radar y los eventos críticos: requiere su aprobación explícita.

**Esfuerzo.** A: una línea de texto y 1 prueba. B: una sesión con unas 5
pruebas (perfil, radar, documento, eventos e historial).

---

## 7 · Meta cambiada después de confirmar

**Problema.** Si una cuenta de administración sube la meta de un objetivo, un
objetivo ya confirmado sigue «confirmado» bajo la meta nueva.

**Comportamiento actual (verificado).**

- La meta es del programa. La cambia una cuenta de administración, con motivo,
  y queda en la auditoría (`progress_store.py:574-591`).
- Confirmar exige alcanzar la meta vigente (`progress_store.py:604`). Pero el
  estado «confirmed» ya no se compara con la meta nueva
  (`progress_store.py:329-333`).
- La tabla muestra la cuenta contra la meta actual
  (`progress_portal.py:76-78` y `114`). El detalle muestra la del momento de
  confirmar (`progress_portal.py:105-107`).
- La docencia puede reabrir a mano (`progress_store.py:620`).

**Por qué importa.** «3/5 · Confirmed» parece una contradicción, y nada avisa
que la meta cambió.

**Ejemplo mínimo.** R1 tiene R2-01 confirmado con 3/3, y la meta de R2-01 sube
a 5. La tabla de R1 dice «3/5 · Confirmed». El detalle dice «At confirmation:
3/3».

**Opciones.**

- **A.** Mantener «Confirmed» y agregar una marca: «confirmado con una meta
  anterior (3/3; meta actual 5)». Nada cambia de estado por sí solo.
- **B.** Reabrir automáticamente toda confirmación que quede bajo la meta
  nueva.
- **C.** Dejarlo como está.

**Recomendación.** A.

**Riesgo.** B deshace juicios docentes por un cambio del programa, sin que
nadie los revise. A sólo informa, y la docencia decide si reabre.

**Esfuerzo.** Una sesión corta con 2 pruebas.

---

## Plantilla de respuesta

Marque una opción por línea. En L-F02, la respuesta A, y en el retiro, la B,
son su aprobación explícita para tocar el radar.

```
DF-24 · respuesta de Nicolás · fecha: ________

I-F02  exportación sin revisor ............... A / B / C / otra: ______
L-F02  revisión elegida por hora (RADAR) ..... A / B / C / otra: ______
I-F18  foto de confirmaciones antiguas ....... A / B / C / otra: ______
L-F07  C14 abierto sin declaración ........... A / B / C / D / otra: ______
Observación anulada .......................... A / B / C / otra: ______
Retiro de rúbrica confirmada ................. A / B (RADAR) / C / otra: ______
Meta cambiada tras confirmar ................. A / B / C / otra: ______
```

**Respuesta recomendada, en una línea:** «I-F02 A · L-F02 A · I-F18 B · L-F07 B
(D después) · anulada A · retiro A · meta A».
