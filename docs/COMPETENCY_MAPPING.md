# Correspondencia de desafíos y competencias

Esta es una correspondencia educativa local entre conductas observables en el
simulador y componentes específicos de los documentos oficiales. Los sesgos no
son EPAs. El objetivo del caso ofrece una oportunidad de observar razonamiento;
no permite concluir que un residente presentó ese sesgo. Los textos descriptivos
del catálogo son formulaciones locales, no reproducciones de las rúbricas.

## Fuentes y localización

Consultadas el 13 de septiembre de 2026. Se fija la edición para permitir auditar
cada observación, sin afirmar que sea la edición aplicable a todas las cohortes.
No se incluyen copias de los documentos en la aplicación.

- [ACGME: Emergency Medicine Milestones](https://www.acgme.org/globalassets/pdfs/milestones/emergencymedicinemilestones.pdf): revisión febrero de 2021, implementación julio de 2021, hoja versión 2.1. PC1 p. 7, PC2 p. 8, PC3 p. 9, PC4 p. 10, PC5 p. 11, PC6 p. 12 y MK2 p. 16. Todas son páginas físicas del PDF; las páginas impresas respectivas son 1–6 y 10.
- [Royal College: Emergency Medicine EPA Guide](https://www.royalcollege.ca/content/dam/documents/ibd/emergency-medicine/epa-guide-emergency-med-e.pdf): 2018, versión 1.1, revisión editorial 1 de noviembre de 2018, 59 páginas. C5 pp. 25–26 y TP6 p. 57. Cada enlace del catálogo identifica además el número de ítem dentro de los hitos relevantes de la EPA.

ACGME aporta dimensiones de desarrollo y Royal College actividades
profesionales con componentes CanMEDS. Su conexión con el desafío es nuestra
interpretación educativa, no una equivalencia oficial entre ambos marcos.

## Matriz de observación

| ID local / desafío | Conducta que debe comprobar el docente | ACGME | Royal College: EPA, competencia e ítem |
|---|---|---|---|
| R1-05 / anclaje | Contrasta su primera explicación con nuevos datos y explica la revisión del manejo. | PC4, MK2, PC6 | C5: ME 1.6 (1), ME 2.4 (6); TP6: ME 4.1 (4) |
| R1-06 / cierre prematuro | Comprueba lo que persiste o puede recurrir después de la respuesta inicial. | PC6, PC4, MK2 | C5: ME 2.4 (6); TP6: ME 4.1 (4) |
| R2-02 / confirmación | Busca e interpreta información que puede debilitar su hipótesis y modifica su plan cuando corresponde. | PC3, PC4, MK2 | C5: ME 1.6 (1), ME 2.2 (4, 5) |
| R2-03 / disponibilidad | Justifica el manejo con datos del paciente actual y contrasta el contexto de casos recientes simulado. | PC4, MK2 | C5: ME 1.6 (1), ME 2.2 (4) |
| R1-07 / encuadre | Distingue la interpretación del traspaso de la información obtenida en su propia evaluación. | PC2, PC4, MK2 | C5: ME 2.2 (2, 3), COM 2.3 (8) |
| R2-04 / representatividad | Considera alternativas relevantes aunque la presentación se aleje del patrón esperado. | PC1, PC4, MK2 | C5: ME 1.6 (1), ME 2.2 (4) |
| R2-05 / satisfacción de búsqueda | Explicita las necesidades que siguen abiertas después de un primer hallazgo positivo. | PC4, PC6, MK2 | C5: ME 2.4 (6); TP6: ME 4.1 (4) |
| R3-01 / impulso de actuar | Contrasta beneficio, daño y respuesta observada antes de decidir otra intervención o reevaluar. | PC5, PC6, MK2 | TP6: ME 2.1 (2), ME 3.3 (3), ME 4.1 (4) |

C5 se refiere al manejo de condiciones de urgencia y TP6 al manejo bajo
incertidumbre. Para R3-01, la conexión con PC5 solo es observable si el encuentro
incluye una decisión farmacológica. Otras conexiones también requieren revisar
que la oportunidad existió y qué conducta se documentó; no deben acreditarse
todos los códigos de una fila por completar el caso.

## Registro y criterio docente

`competency_mapping.py` conserva versiones, URL, página, EPA e ítem exactos.
`mapping_for_challenge` devuelve esas referencias junto con conductas y requisitos
de evidencia; `cognitive_catalog.py` y `objectives.py` las comparten sin duplicar
la fuente de verdad.

Cada nuevo ID R* es un **componente local de razonamiento en simulación**. Se
habilita únicamente para el desafío documentado en el intento. Metadatos
contradictorios impiden habilitarlo. Debe citarse al menos una decisión registrada;
una reflexión aislada no sustituye el desempeño durante el encuentro. El docente
puede conservar observaciones insatisfactorias. La falta de documentación debe
distinguirse de una conducta ausente y de una oportunidad no observada.

El docente vincula la evidencia a las conductas, registra contexto y ayuda
recibida y confirma su juicio. Las conexiones curriculares no asignan niveles
ACGME, etapas de residencia, certificaciones ni logros de EPAs completas. No
acreditan destrezas manuales, comunicación o liderazgo real de equipos.

Los ocho nuevos componentes utilizan inicialmente **3 observaciones
satisfactorias como meta local configurable de revisión**. Es una elección de
configuración de la aplicación, no un requisito de ACGME/Royal College ni un
umbral validado de competencia. No limita observaciones posteriores. Se
preservan los objetivos clínicos y las metas previamente configuradas.
