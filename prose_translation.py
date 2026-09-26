"""The model's prose in the reader's language, translated once and kept (faculty, 2026-09-26).

The analyses -- the Management Trace, the faculty brief, the rubric proposal --
are generated in English by contract, and that original stays canonical: it is
what the evaluation, the correction log and the reproducibility checks read.
The faculty asked (2026-09-26) that whatever the app stores can be read in
English or Spanish, and chose to translate the model's prose when it is asked
for rather than generating it twice.

* A document written in Spanish collects the exact English sentences it would
  print -- after the recorded corrections -- and asks for the ones not yet
  translated, in one call.
* Each translation is stored by the hash of the English it came from and the
  prompt that made it, so it is paid for once and reused by every later
  document; a corrected sentence is new English and is translated again rather
  than served stale.
* Nothing is translated for an English reader, nothing is translated without a
  configured key, and a sentence that could not be translated stays in English
  -- the document says which of the two it is.

The resident's quoted words are never translated: the prompt keeps anything in
quotation marks exactly as written, and a document never sends the learner's
own entries here, only the model's sentences about them.
"""
from __future__ import annotations

import hashlib
import json
import time

PROMPT_VERSION = "prose-es-1"
DEFAULT_MODEL = "gpt-5-mini"
#: One call carries at most this much English; a longer document makes more calls.
MAX_BATCH_CHARS = 18_000
MAX_BATCH_ITEMS = 60

INSTRUCTIONS = """You translate the prose of a clinical-education report from English to Spanish, for physicians \
in Chile. Each input item is one passage; return exactly one translation for each, with the same id.

Rules, all of them strict:
1. Faithful: never add, remove, soften or strengthen anything. Keep every hedge ("may", "appears", "the record \
does not establish"), every negation and every qualifier.
2. Keep exactly as written: numbers, times, units, doses, drug names, abbreviations (SpO2, PaCO2, POCUS, ECG, \
ICU), evidence labels such as "D2", "D1 · 00:04" or "trace:3", and identifiers in brackets.
3. Keep exactly as written any text inside quotation marks (" ", “ ”, « »): it is a learner's own words.
4. Register: neutral Latin American clinical Spanish that reads naturally in Chile; address the learner as \
"usted" when the English addresses "you".
5. Return plain text only, no notes."""


def _digest(text, language):
    return hashlib.sha256(f"{PROMPT_VERSION}\n{language}\n{text}".encode("utf-8")).hexdigest()


class ProseTranslations:
    """Stored translations of the model's prose, shared by every document."""

    def __init__(self, accounts):
        self.accounts = accounts
        self._execute = accounts._execute
        if not accounts.schema_ready("prose_translations"):
            with accounts._transaction(write=True) as connection:
                self._execute(connection, """CREATE TABLE IF NOT EXISTS mrs_prose_translations (
                    digest TEXT PRIMARY KEY,
                    language TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at BIGINT NOT NULL
                )""")
            accounts.mark_schema_ready("prose_translations")

    def known(self, texts, language):
        """The stored translation of each text that has one."""
        wanted = {_digest(text, language): text for text in texts if text}
        if not wanted:
            return {}
        found = {}
        with self.accounts._transaction() as connection:
            digests = list(wanted)
            for start in range(0, len(digests), 200):
                chunk = digests[start:start + 200]
                marks = ", ".join("?" for _ in chunk)
                for row in self._execute(connection, f"""SELECT digest, source_text, translated_text
                        FROM mrs_prose_translations WHERE digest IN ({marks})""", tuple(chunk)).fetchall():
                    # The stored English must be the English asked about: a hash is
                    # not trusted on its own.
                    if row["source_text"] == wanted.get(row["digest"]):
                        found[row["source_text"]] = row["translated_text"]
        return found

    def save(self, pairs, language, model):
        now = int(time.time())
        with self.accounts._transaction(write=True) as connection:
            for source, translated in pairs.items():
                digest = _digest(source, language)
                exists = self._execute(connection, "SELECT 1 FROM mrs_prose_translations WHERE digest = ?",
                                       (digest,)).fetchone()
                if exists:
                    continue
                self._execute(connection, """INSERT INTO mrs_prose_translations
                    (digest, language, prompt_version, source_text, translated_text, model, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                              (digest, language, PROMPT_VERSION, source, translated, model, now))


def _batches(texts):
    batch, size = [], 0
    for text in texts:
        if batch and (size + len(text) > MAX_BATCH_CHARS or len(batch) >= MAX_BATCH_ITEMS):
            yield batch
            batch, size = [], 0
        batch.append(text)
        size += len(text)
    if batch:
        yield batch


def _schema(count):
    return {"type": "object", "additionalProperties": False, "required": ["items"],
            "properties": {"items": {"type": "array", "minItems": count, "maxItems": count, "items": {
                "type": "object", "additionalProperties": False, "required": ["id", "text"],
                "properties": {"id": {"type": "integer"}, "text": {"type": "string"}}}}}}


def translate(texts, language="es", *, api_key="", model=DEFAULT_MODEL, client=None):
    """Translate these passages in one call per batch; what fails is left out, never guessed."""
    if language != "es" or not texts:
        return {}
    if client is None:
        if not isinstance(api_key, str) or not api_key.strip():
            return {}
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=90.0, max_retries=0)
    done = {}
    for batch in _batches(list(dict.fromkeys(texts))):
        items = [{"id": index, "text": text} for index, text in enumerate(batch)]
        try:
            response = client.responses.create(
                model=model, instructions=INSTRUCTIONS,
                input=json.dumps({"items": items}, ensure_ascii=False),
                text={"format": {"type": "json_schema", "name": "prose_translation",
                                 "schema": _schema(len(items)), "strict": True}},
                max_output_tokens=16_000, store=False)
            output = getattr(response, "output_text", None)
            if getattr(response, "status", None) != "completed" or not isinstance(output, str):
                continue
            rows = json.loads(output).get("items") or []
        except Exception:
            # A provider error may carry request contents; it is not re-raised, and the
            # passages it covered stay in English.
            continue
        for row in rows:
            index = row.get("id") if isinstance(row, dict) else None
            text = row.get("text") if isinstance(row, dict) else None
            if isinstance(index, int) and 0 <= index < len(batch) and isinstance(text, str) and text.strip():
                done[batch[index]] = text.strip()
    return done


def ensure(texts, language, *, store=None, api_key="", model=DEFAULT_MODEL, client=None):
    """Every passage's translation: the stored ones, and the rest asked for once and stored."""
    texts = [text for text in dict.fromkeys(texts) if isinstance(text, str) and text.strip()]
    if language != "es" or not texts:
        return {}
    known = store.known(texts, language) if store is not None else {}
    missing = [text for text in texts if text not in known]
    if missing:
        fresh = translate(missing, language, api_key=api_key, model=model, client=client)
        if fresh and store is not None:
            store.save(fresh, language, model)
        known.update(fresh)
    return known


def secret(name, default=""):
    """The deployment's configuration, read as the rest of the app reads it.

    Offline runs withhold the provider key (``offline_cases``), so a test or a
    rehearsal never buys a translation.
    """
    import os
    try:
        import streamlit as st
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    from offline_cases import withhold
    return withhold(name, str(value or os.environ.get(name, default) or "").strip())


def translator(context, secret=secret):
    """The callable a document is handed: its prose in, the translations out.

    ``secret(name, default)`` reads the deployment's configuration; without a
    key only stored translations are returned.
    """
    store = ProseTranslations(context["store"]) if context and context.get("store") else None
    api_key = secret("OPENAI_API_KEY", "")
    model = secret("MRS_TRANSLATION_MODEL", "") or DEFAULT_MODEL

    def run(texts, language="es"):
        return ensure(texts, language, store=store, api_key=api_key, model=model)
    return run
