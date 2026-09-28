# Próximas acciones (una página)

Al cierre del ciclo 6, 2026-09-28. El detalle está en
`COLA_DECISIONES_AI_ADVISOR.md` (sección «Cierre del ciclo 6»).

## DONE

- **DF-22:** las 9 clases CRITICAL del lector, corregidas por clase en EN/ES.
  - Con 192 pruebas, tres conjuntos ciegos y una revisión adversarial.
  - Esa revisión halló regresiones de las propias correcciones, ya corregidas.
  - Residuos en TD-14 y TD-26.
- **59O-03:** el aviso de ejecución sale sólo de lo que corrió. Una orden
  retenida ya no se pierde con «no sé».
- **L-F01 y L-F04:** el encuentro se lee con su propio caso; el perfil sigue
  la fecha del encuentro.
- **DF-23:** de Winter y `bradycardia_bb_54f`, corregidos.
  `acs_54m_inferior`, sin cambio.
- **DEVELOPMENT HARDENED BASELINE V1** registrado (`validation/BASELINES.md`).
  El baseline español del piloto no se tocó.

## NEEDS NICOLÁS

1. **Antes de un piloto con residentes** (`READINESS_PILOTO_RESIDENCIA.md`:
   WITH CONDITIONS):
   - TD-21: trauma y sobrecarga transfusional (recomendado: excluir la
     hemorragia activa de la regla);
   - TD-26: autorizar la corrección de los hemoderivados que se pierden sin
     aviso;
   - escribir C4 = NO en el banco;
   - uso formativo, con confirmación docente;
   - acceso a staging para probar PostgreSQL.
2. **El piloto de validación** (`validation/pilot_v1/README.md`):
   - revisar los 18 documentos;
   - reclutar a los 6 médicos y enviar.
3. **Tres respuestas de una línea:**
   - DF-24: «I-F02 A · L-F02 A · I-F18 B · L-F07 B (D después) · anulada A ·
     retiro A · meta A».
   - TDFC: «1 approve / 2 approve / 3 approve / 4 approve / 5 approve (54m
     tras DF-20) / 6 approve / 8 approve».
   - `acs_54m_inferior`: C14 NO (recomendado) o YES.
4. **Cuando pueda:** las filas 3 a 11 de DF-23, en
   `AUDITORIA_DF23_CICLO6.md`.

## WAITING FOR EXTERNAL DATA

- **Los documentos de los médicos del piloto.** Se miden primero contra el
  SPANISH PILOT BASELINE (`939978a`) y después contra el HARDENED BASELINE V1.
- **La fidelidad externa del lector.** De ella depende el orden de TD-14.

## DEFERRED

- **Nada TD/F/C en el banco** hasta sus respuestas (DF-21).
- **Las brechas del banco (DF-25)**, priorizadas y sin implementar.
- **Optimizar la cola docente (TD-09)**, antes de cohortes de más de ~20
  residentes.
- **C2, C15, los vínculos PARTIAL, el *faculty override* y −3**, sin cambio.
- **El lector**, salvo lo que se mida en el piloto: primero medir y después
  corregir (§89).
