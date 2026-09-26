"""The language an encounter's documents are written in (faculty, 2026-09-26).

"If the encounter is run in Spanish, the PDFs are generated in Spanish; if it
is run in English, in English. Whatever the app stores can be seen in either."

* An encounter keeps the language it was played in, ``encounter_language``:
  the reader's language when the encounter closes (``app.begin_decision_review``),
  saved with the rest of the session. It is metadata beside the evidence and
  enters no analysis: ``build_analysis_source`` reads named fields only.
* Its documents are written in that language unless their reader chooses the
  other one, beside the download. The same stored record is presented again,
  never regenerated.
* An encounter closed before this recorded no language, and none is guessed
  for it: its documents follow their reader's choice, as they always did.
"""
import language

FIELD = "encounter_language"

_PLAYED = {
    "en": {"en": "Played in English.", "es": "Played in Spanish."},
    "es": {"en": "Jugado en inglés.", "es": "Jugado en español."},
}
_NOT_RECORDED = {
    "en": "This encounter did not record its language (it closed before 2026-09-26); "
          "the documents use the one you choose.",
    "es": "Este encuentro no registró su idioma (se cerró antes del 2026-09-26); "
          "los documentos usan el que elijas.",
}


def recorded(session):
    """The language the encounter was played in, or None when it recorded none."""
    value = session.get(FIELD) if isinstance(session, dict) else None
    return value if value in language.LANGUAGES else None


def of_record(record):
    """The recorded language of a saved attempt."""
    payload = (record or {}).get("payload") if isinstance(record, dict) else None
    return recorded((payload or {}).get("session") if isinstance(payload, dict) else None)


def default(session):
    """The encounter's language, or the reader's when the encounter recorded none."""
    return recorded(session) or language.current()


def choose(key, session):
    """The reader's choice for this encounter's documents, starting from the encounter's language."""
    import streamlit as st
    codes = list(language.LANGUAGES)
    played = recorded(session)
    reader = language.current()
    choice = st.radio("Idioma del documento · Document language", codes,
                      index=codes.index(played or reader), key=key, horizontal=True,
                      format_func=lambda code: language.LANGUAGES[code])
    st.caption(_PLAYED[reader][played] if played else _NOT_RECORDED[reader])
    return choice
