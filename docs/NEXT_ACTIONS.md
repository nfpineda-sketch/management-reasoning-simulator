# Próximas acciones (una página)

Al cierre del ciclo 5 y su extensión nocturna, 2026-09-28. El detalle está en
`COLA_DECISIONES_AI_ADVISOR.md`.

## Lo que usted necesita hacer

1. **Decidir `acs_54m_inferior` (DF-20).** ¿VD comprometido (recomendado: A),
   VD normal (B), ambos (C) o intención indeterminable (D)? Si elige A, falta
   aprobar el texto del VD y de la VCI. Documento:
   `AUDITORIA_ACS_54M_INFERIOR.md`.
2. **Dos respuestas sobre el lector (DF-22).** La auditoría nocturna encontró
   9 clases de oración que pierden una orden de primera línea.
   - ¿El piloto las mide sin registrarlas antes como defectos conocidos?
     (recomendado: sí)
   - ¿Se corrige antes de un piloto con residentes el aviso «Urgent
     intervention executed» que aparece cuando nada corrió? (recomendado: sí)
3. **Piloto de validación v1: su parte** (`validation/pilot_v1/README.md`):
   - revisar los 18 documentos en Word;
   - reclutar a los 6 médicos y enviar;
   - cuando vuelvan, guardarlos sin abrir, fuera del repositorio.
4. **Cuando pueda, en este orden:**
   - DF-23: inconsistencias clínicas; primero el POCUS de de Winter, que es
     C14 YES;
   - DF-24: correcciones longitudinales;
   - DF-21: TD/F/C, 8 decisiones;
   - DF-25: brechas del banco.

   Ninguna bloquea el piloto.

## Lo que el AI Advisor puede hacer sin usted

- Aplicar DF-20, DF-23 o DF-24 cuando usted decida: el dato o el código, la
  traducción y las pruebas.
- Correr el sorteo y la ingesta cuando vuelvan los documentos: son comandos
  deterministas.
- Anotar no: la anotación de referencia es clínica.

## Lo que estamos esperando

- Los documentos de los médicos del piloto.
- Sus decisiones sobre DF-20 y DF-22.

## Lo que está bloqueado

- **Medir la fidelidad externa del lector.** Espera los documentos.
- **Retirar la transición de TD1, F1, C1, C3 y C4.** Espera DF-21.
- **C14 en `acs_54m_inferior`.** Espera DF-20.

## Lo que no debe tocarse todavía

- **El SPANISH PILOT BASELINE (`939978a`) y el ENGLISH VALIDATION BASELINE
  (`ec1c77f`).** Se mide ahí.
- **Los 18 documentos del piloto.** Son PILOT MATERIAL V1.
- **Puntajes, D1–D5, eventos críticos, −3 y radar.**
- **C2, C15 y los 9 vínculos PARTIAL inactivos.**
- **El lector, por errores que no vengan del piloto.** Tampoco por los de la
  auditoría nocturna (59I). Se prioriza con `PRIORIZACION_POST_PILOTO.md`.
