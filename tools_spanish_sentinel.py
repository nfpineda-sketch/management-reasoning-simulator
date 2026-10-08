"""The Spanish sentinel: what a resident sees in a Spanish encounter, checked for English (B-5, IG-0).

X-1 (faculty, 2026-10-07, §10): an inventory read from the code cannot prove that
nothing was left out, so the candidate is checked by playing it. This tool opens
each pilot case on the real page (AppTest, a throwaway SQLite database, no
network, no provider key), with the interface in Spanish and the faculty's
approved narrative installed, and walks the encounter a resident walks: the
dashboard, the room, a question to the patient and a history topic, every region
of the examination, an order held for its reasoning, orders the room has to ask
about, cancelling, the case's definitive treatment, a wait, a reassessment, the
ECG and the close. Families whose turning points come late get their own walk
(the bradycardia arrest, the anaphylactic reaction that returns, the arrest
after a dose of adrenaline that did not hold).

At every step it collects the text the page shows -- markdown and HTML, captions,
notices, buttons, labels, placeholders, help, options, expanders -- and reports
each line with English in it. A word is English when the page's English sources
use it and no approved Spanish source does (``english_vocabulary`` minus
``spanish_vocabulary``), or when it is one of the words no Spanish sentence of
the room ever uses (``ALWAYS_ENGLISH``: English function words and the drug names
whose Spanish differs, V-9).

Left out, on purpose, and only these:

* what the resident wrote -- exactly the texts this walk typed, wherever the room
  quotes them, and quoted «…» words: it is quoted, never translated. A ``YOU``
  entry the room composes itself («Examine: …», «Ask about …») is not the
  resident's writing and is checked like any other line;
* the canonical names the faculty kept in English (``CANONICAL``): the product
  and the Management Trace;
* lines bilingual by design (``BILINGUAL``): the language selector, which has to
  be found by a reader of either language.

A line the room shows in English because the faculty has not yet decided its
Spanish is not an exception and is not left out: it is reported as pending
(``PENDING_FACULTY_WORDING``, B-5 IG-5; ``docs/revision/B5_IG5_PENDIENTES_DOCENTES.md``),
apart from any other line with English, which is unintended. Texts the walk does not
reach and that still wait for their Spanish are listed apart
(``PENDING_OUTSIDE_THE_WALK``); the report names them, and the sentinel is not
complete while one is open.

Nothing is translated, approved or repaired here. Usage::

    python3 tools_spanish_sentinel.py --out DIR [CASE ...]    # every pilot case by default
"""
from __future__ import annotations

import argparse
import ast
import html
import json
import os
import re
import sys
import tempfile
import time
import uuid
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP = ROOT / "app.py"

#: English function words: never part of a Spanish sentence of the room (tools_engine_spanish). «has» is left
#: out: it is also Spanish («No has registrado un destino»).
FUNCTION_WORDS = frozenset("""
the and with after of is are was were have had this that these those it its they their from for
by at on to into over than then while without within shows show showing remains still now not your
you please which when where what will would should can could may might must do does did an as or if
""".split())
#: The canonical drug names whose Spanish differs (V-9, XR-06): an encounter in Spanish never shows them.
V9_DIFFERENT = frozenset("""
norepinephrine epinephrine dobutamine nitroglycerin amiodarone atropine aspirin heparin enoxaparin
tenecteplase alteplase streptokinase etomidate ketamine dexmedetomidine rocuronium succinylcholine
vecuronium cisatracurium morphine fentanyl ibuprofen ketorolac metamizole albuterol ipratropium
prednisone methylprednisolone hydrocortisone dexamethasone ceftriaxone azithromycin vancomycin
dextrose thiamine glucagon naloxone octreotide pantoprazole omeprazole furosemide crystalloid
""".split())
ALWAYS_ENGLISH = FUNCTION_WORDS | V9_DIFFERENT
#: Codes and units written the same in both languages (X1-0, point 2, faculty, 2026-10-07).
#: IPAP and EPAP are the two pressures of BiPAP, written the same way in Spanish, like CPAP and BiPAP
#: (X1-0, point 2; classified as codes in IG-5, not a faculty decision of their own).
CODES = frozenset("iv io im sc po ml min mcg kg mg cm fio peep cpap bipap ipap epap ecg pocus efast fast".split())

#: Names the faculty kept as they are in Spanish (X-1, P-04: «Management Trace» is a proper name).
CANONICAL = ("MANAGEMENT REASONING SIMULATOR", "Management Reasoning Simulator", "Management Trace")
#: Lines that are bilingual by design: the language selector (faculty, 2026-09-27) and the language a
#: document is written in (``document_language.choose``, faculty, 2026-09-26), which a reader of either
#: language has to find.
BILINGUAL = (
    "Idioma · Language",
    "Fijo durante el encuentro: es el idioma en que se inició. · Fixed during the encounter: the language it "
    "started in.",
    "English",
    "Idioma del documento · Document language",
)

#: Modules whose English is never read on screen: the tests, the tools, the regression scripts and
#: the language tables themselves (their English is taken separately, below).
_NOT_SCREEN = re.compile(r"^(test_|tools_|regression_|run_regressions|conftest|language\.py$|report_language\.py$|"
                         r"spanish_drafts\.py$|history_topics\.py$)")
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def _words(text):
    return {word.lower() for word in _WORD.findall(str(text or "")) if len(word) > 1}


#: A template's slot ({drug}, {given}…): a name in the code, not a word the Spanish says.
_SLOT = re.compile(r"\{\w*\}")


def _spanish_words(text):
    """The words of an approved Spanish text, without its templates' slots."""
    return _words(_SLOT.sub(" ", str(text or "")))


#: A literal that is a pattern (the bilingual reader's, among others), not a sentence anyone reads.
_PATTERN = re.compile(r"\\[bsdwSW]|\(\?|\[\^|\]\+|\]\*")
#: A literal written in Spanish: the room's own Spanish is counted from its approved sources only.
_SPANISH_MARK = re.compile(r"[áéíóúñ¿¡«»ÁÉÍÓÚÑ]")


def _constants(path):
    """Every string literal of a module that could be read in English: no patterns, nothing in Spanish."""
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
            if _PATTERN.search(text) or ("|" in text and " " not in text) or _SPANISH_MARK.search(text):
                continue
            found.append(text)
    return found


@lru_cache(maxsize=None)
def english_vocabulary():
    """The words the page's English sources use: the runtime modules, the catalog's English, the narrative's."""
    import case_text
    import language
    import report_language
    import rubric
    found = set()
    for path in sorted(ROOT.glob("*.py")):
        if not _NOT_SCREEN.match(path.name):
            for text in _constants(path):
                found |= _words(text)
    found |= set().union(*(_words(key) for key in report_language.ES))
    found |= set().union(*(_words(pattern.pattern) for pattern, _ in language._COMPILED))
    for passages in case_text.current_english().values():
        for text in passages.values():
            found |= _words(text)
    for domain in rubric.DOMAINS.values():
        found |= _words(domain.get("asks")) | set().union(*(_words(t) for t in domain.get("levels", {}).values()))
    return frozenset(found)


def _spanish_values(module, names_like=("_ES", "_es")):
    """The values of a module's Spanish tables and sentences (named ``*_ES``)."""
    found = set()
    for name, value in vars(module).items():
        if name.endswith(names_like) and isinstance(value, dict):
            for item in value.values():
                found |= _spanish_words(item if isinstance(item, str) else json.dumps(item, ensure_ascii=False))
        elif name.endswith(names_like) and isinstance(value, str):
            found |= _spanish_words(value)
        elif name.endswith(names_like) and isinstance(value, (tuple, list)):
            # A table of (pattern, Spanish) pairs, such as the engine's findings: only the Spanish counts.
            for pair in value:
                if isinstance(pair, (tuple, list)) and len(pair) == 2 and isinstance(pair[1], str):
                    found |= _spanish_words(pair[1])
    return found


#: The room's modules that keep Spanish tables of their own (X-1, IG-5): the bed space, the monitor
#: and the ECG, the record's labels and the treatments panel.
_SPANISH_MODULES = ("history_topics", "resuscitation_room", "clinical_scene", "report_presentation", "family_reports")


@lru_cache(maxsize=None)
def spanish_vocabulary():
    """The words the approved Spanish uses: the narrative, the rubric, the catalogs and the room's rules.

    Only what the room can show: the drafts (``spanish_drafts``) count once they are active rules.
    """
    import case_text
    import language
    import report_language
    import rubric_text
    found = set()
    for rows in case_text.passages("es").values():
        for row in rows.values():
            found |= _spanish_words(row.get("es"))
    for rows in rubric_text.drafts("es").values():
        for row in rows.values():
            found |= _spanish_words(row.get("es"))
    for value in report_language.ES.values():
        found |= _spanish_words(value)
    for _, replacement in language._RULES:
        if isinstance(replacement, str):
            found |= _spanish_words(replacement)
    for value in language.MESSAGES.values():
        found |= _spanish_words(value)
    found |= _spanish_values(language)
    import importlib
    for name in _SPANISH_MODULES:
        found |= _spanish_values(importlib.import_module(name))
    for table in (getattr(language, "ENGINE_SENTENCES", {}).get("es", {}),):
        for value in table.values():
            found |= _spanish_words(value)
    return frozenset(found)


#: Lines found in English whose Spanish the faculty has not decided (B-5, IG-5; TD-86;
#: ``docs/revision/B5_IG5_PENDIENTES_DOCENTES.md``). Not exceptions: decisions pending. Each entry is
#: (item, pattern, English words it may carry): with ``None`` the pattern must match the whole line;
#: otherwise it must occur in the line and the line's English must be only those words.
#: Empty since the faculty decided ES-P1 to ES-P7 (2026-10-08): every line with English the walk
#: finds is now unintended.
PENDING_FACULTY_WORDING = ()

#: Texts the room can show in English, outside the walk, that wait for the faculty's Spanish
#: (TD-86). The walk does not reach them; they are listed so that the sentinel never reads as
#: complete while one is open (``test_spanish_sentinel.py``), and none is an exception. Empty
#: since the faculty decided ES-P8 to ES-P13 (2026-10-08): ES-P8, ES-P9, ES-P10, ES-P12 and
#: ES-P13 are said in Spanish, and ES-P11 («endoscopy performed») stays canonical data that no
#: resident-facing room shows.
PENDING_OUTSIDE_THE_WALK = {}


def pending_item(line, english):
    """The pending faculty item a line with English belongs to, or None when its English is unintended."""
    for item, pattern, words in PENDING_FACULTY_WORDING:
        if words is None and pattern.fullmatch(str(line)):
            return item
        if words is not None and pattern.search(str(line)) and set(english) <= words:
            return item
    return None


def english_words(line):
    """The English words a Spanish reader would see in this line; empty when it reads in Spanish."""
    text = str(line or "")
    for name in CANONICAL:
        text = text.replace(name, " ")
    text = re.sub(r"«[^»]*»", " ", text)  # quoted: the resident's own words
    words = _words(text)
    english_only = english_vocabulary() - spanish_vocabulary()
    return sorted(word for word in words if word not in CODES and (word in ALWAYS_ENGLISH or word in english_only))


# --- the page ------------------------------------------------------------------------

_TAG = re.compile(r"<[^>]+>")


def visible(at):
    """Every text the page shows now: [(where, line)], the resident's own typing left out."""
    texts = []

    def add(kind, value):
        if value is None:
            return
        value = str(value)
        if "<" in value and ">" in value:
            value = re.sub(r"(?is)<style.*?</style>|<script.*?</script>|<svg.*?</svg>", " ", value)
            value = html.unescape(_TAG.sub("\n", value))
        for line in value.split("\n"):
            line = re.sub(r"\s+", " ", line).strip()
            if not line or re.search(r"[{};]\s*$|^[.#@\[/*]|^[a-z-]+:[^ ]|!important|data-testid", line):
                continue  # stylesheet text, not something a reader sees
            texts.append((kind, line))

    for kind in ("markdown", "caption", "warning", "info", "error", "success", "title", "header", "subheader"):
        for item in getattr(at, kind, []):
            add(kind, item.value)
    for item in at.button:
        add("button", item.label)
        add("button.help", getattr(item, "help", None))
    for kind in ("radio", "selectbox", "multiselect"):
        for item in getattr(at, kind, []):
            add(kind + ".label", item.label)
            add(kind + ".help", getattr(item, "help", None))
            for option in item.options:
                add(kind + ".option", option)
    for kind in ("text_area", "text_input", "number_input", "checkbox", "toggle", "slider"):
        for item in getattr(at, kind, []):
            add(kind + ".label", item.label)
            add(kind + ".placeholder", getattr(item, "placeholder", None))
            add(kind + ".help", getattr(item, "help", None))
    for kind in ("expander", "tabs", "tab", "metric"):
        for item in getattr(at, kind, []):
            add(kind, getattr(item, "label", None))
    return texts


def _resident_lines(at, typed=()):
    """What the resident wrote, as the room quotes it, so that it is never counted.

    Only what was typed: the walk's own orders and questions, and each piece of them the room
    quotes on its own (an order split into its clauses). An entry the room writes in the
    resident's place («Examine: General appearance») is the room's own words.
    """
    typed = [str(text).strip() for text in typed if str(text or "").strip()]
    found = set(typed)
    for event in at.session_state["events"] or []:
        text = str(event.get("text") or "").strip()
        if event.get("kind") in ("you", "reasoning_completion") and any(
                text == written or (len(text) > 12 and text in written) for written in typed):
            found.add(text)
    return found


def findings(texts, resident=()):
    """[(where, line, words)] for each line with English, the declared exceptions left out."""
    found = []
    for kind, line in texts:
        if line in BILINGUAL or any(line.strip() == quoted or (quoted and quoted in line) for quoted in resident):
            continue
        words = english_words(line)
        if words:
            found.append((kind, line, words))
    return found


def _labels(english):
    """The label a widget shows in English and in Spanish, whichever the page uses."""
    import language
    import report_language
    return {english, report_language.t(english, "es"), language.say(english, "es")}


def _widget(elements, english):
    wanted = _labels(english)
    for item in elements:
        if item.label in wanted:
            return item
    raise LookupError(f"no widget {english!r}; the page has {[item.label for item in elements]}")


class Walk:
    """One pilot case on the page, in Spanish, recording what each step shows."""

    def __init__(self, variant, challenge, workdir):
        self.variant, self.steps, self.typed = variant, [], []
        self._env = {"MRS_AUTH_MODE": "accounts", "MRS_ALLOW_LOCAL_SQLITE": "true", "MRS_OFFLINE_CASES": "1",
                     "MRS_DEFAULT_VARIANT": variant, "MRS_LANGUAGE": "es", "HOME": str(workdir),
                     "MRS_DATABASE_URL": f"sqlite:///{Path(workdir) / (variant + '.sqlite3')}"}
        self._challenge = challenge
        self.at = None

    def __enter__(self):
        self._saved = {name: os.environ.get(name) for name in [*self._env, "OPENAI_API_KEY"]}
        os.environ.update(self._env)
        os.environ.pop("OPENAI_API_KEY", None)
        import curriculum_runtime
        self._assign = curriculum_runtime.assign_challenge
        challenge = self._challenge
        curriculum_runtime.assign_challenge = lambda *a, **k: {
            "challenge_id": challenge, "reason": "sentinel", "assignment_seed": 17,
            "competence_decision": "Not assessed automatically"}
        return self

    def __exit__(self, *exc):
        import curriculum_runtime
        curriculum_runtime.assign_challenge = self._assign
        for name, value in self._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        return False

    def snap(self, name):
        resident = sorted(_resident_lines(self.at, self.typed)) if "events" in self.at.session_state else []
        self.steps.append({"step": name, "texts": visible(self.at), "resident": resident,
                           "exception": [str(e.value) for e in self.at.exception] if self.at.exception else None})

    def open(self):
        from account_store import AccountStore
        from resident_profile import ProfileStore
        from streamlit.testing.v1 import AppTest
        store = AccountStore(os.environ["MRS_DATABASE_URL"], allow_sqlite=True)
        with store._transaction(write=True) as connection:
            user_id = uuid.uuid4().hex
            # A name with no letters a word list could know: the sidebar shows it as written.
            store._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                           (user_id, f"centinela_{int(time.time() * 1000) % 10 ** 6}", "unused-fixture-hash",
                            "resident", 3, int(time.time())))
            token = store._new_session(connection, user_id)
        ProfileStore(store).decline(token)
        self.at = AppTest.from_file(str(APP), default_timeout=300)
        self.at.session_state["_account_token"] = token
        self.at.session_state["presentation_language"] = "es"
        self.at.run()
        self.snap("panel de inicio")
        _widget(self.at.button, "Begin Encounter").click().run()
        drawn = ((self.at.session_state["state"] or {}).get("encounter_spec") or {}).get("variant_id")
        if drawn != self.variant:
            raise LookupError(f"the launch drew {drawn!r}, not {self.variant!r}")
        self.snap("sala abierta")

    def mode(self, value):
        _widget(self.at.radio, "Encounter").set_value(value).run()

    def send(self, text, name=None):
        self.mode("Treat")
        self.typed.append(text)
        _widget(self.at.text_area, "Enter your clinical reasoning and/or actions").set_value(text)
        _widget(self.at.button, "Send").click().run()
        self.snap(name or f"orden: {text}")

    def ask(self, question):
        self.mode("Talk")
        box = [item for item in self.at.text_input]
        if box:
            self.typed.append(question)
            box[0].set_value(question)
            _widget(self.at.button, "Ask").click().run()
        self.snap(f"pregunta: {question}")
        topics = [item for item in self.at.selectbox if item.label in _labels("Explore")]
        if topics:
            _widget(self.at.button, "Ask about this topic").click().run()
            self.snap("tema de la historia")

    def examine_all(self):
        self.mode("Examine")
        regions = list(_widget(self.at.selectbox, "Examine").options)
        values = []
        import family_engine
        for value in family_engine.available_regions(self.at.session_state["state"]):
            values.append(value)
        for region in values:
            self.mode("Examine")
            _widget(self.at.selectbox, "Examine").set_value(region).run()
            _widget(self.at.button, "Examine patient").click().run()
            self.snap(f"examen: {region}")
        return regions

    def click(self, english):
        _widget(self.at.button, english).click().run()
        self.snap(f"botón: {english}")

    def try_click(self, english):
        try:
            self.click(english)
            return True
        except LookupError:
            return False


REASONING_ES = ("Creo que el problema principal es la descompensación que presenta. Mi prioridad es estabilizarlo. "
                "Espero que mejoren la perfusión y la saturación. Reviso presión, frecuencia cardíaca, saturación y "
                "conciencia en 15 minutos. ")


def walk(variant, workdir):
    """The steps of one case: what each one showed, with the lines that still carry English."""
    import pilot_acceptance as acceptance
    family = acceptance.family_of(variant)
    with Walk(variant, acceptance.LAUNCH[family], workdir) as page:
        try:
            page.open()
            page.ask("¿Qué le pasó?")
            page.examine_all()
            # An order with no reasoning: held at the gate (G-01 to G-10).
            page.send("Administra oxígeno por naricera a 2 L/min.", "orden sin razonamiento")
            page.try_click("Cancel pending orders")
            # Orders the room has to ask about (X1-C01, X1-C02), then cancelled (X1-C32, X1-C33).
            page.send(REASONING_ES + "Inicia noradrenalina.", "orden sin dosis")
            page.try_click("Cancel pending orders")
            page.send(REASONING_ES + "Administra un antibiótico IV.", "orden sin fármaco")
            page.try_click("Cancel pending orders")
            scripts = acceptance.scripts(variant)
            if variant in ("bradycardia_ccb_68m", "bradycardia_avb3_78f"):
                # The arrest of an untreated bradycardia (K-E6, TD-85 a).
                page.send(REASONING_ES + "Espero 90 minutos.", "espera hasta el paro")
                page.send("Espero 60 minutos.", "espera tras el paro")
            elif variant == "anaphylaxis_29f":
                # The reaction that returns after it settled (K-E8, TD-85 b).
                page.send(REASONING_ES + scripts["correct"], "tratamiento definitivo")
                for _ in range(3):
                    page.send("Espero 60 minutos.", "espera de la reacción bifásica")
            elif variant == "anaphylaxis_63m_betablocked":
                # One dose that does not hold the reaction (K-18, K-E5).
                page.send(REASONING_ES + "Administra adrenalina 0.5 mg IM.", "una dosis de adrenalina")
                page.send("Espero 90 minutos.", "espera hasta el paro")
            else:
                page.send(REASONING_ES + scripts["correct"], "tratamiento definitivo")
                page.send("Espero 20 minutos.", "espera")
                page.send("Reevalúa al paciente.", "reevaluación")
            page.examine_all()
            page.mode("Tests")
            page.try_click("ECG")
            page.snap("exámenes")
            if page.try_click("Complete Encounter & Begin Review"):
                # With no destination recorded the room asks first, and never blocks (decision 9).
                page.try_click("Finish now")
            page.snap("revisión")
        except Exception as error:  # the walk's own failure, reported as such and never as a pass
            page.steps.append({"step": "STOPPED", "texts": [], "resident": [],
                               "exception": [f"{type(error).__name__}: {error}"]})
    rows = []
    for step in page.steps:
        for kind, line, words in findings(step["texts"], step.get("resident") or ()):
            rows.append({"step": step["step"], "where": kind, "line": line, "english": words})
    stopped = [step for step in page.steps if step.get("exception")]
    return {"case": variant, "steps": len(page.steps), "english": _unique(rows),
            "stopped": [{"step": s["step"], "exception": s["exception"]} for s in stopped]}


def _unique(rows):
    seen, out = set(), []
    for row in rows:
        key = (row["where"], row["line"])
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, help="a new directory for the report")
    parser.add_argument("cases", nargs="*")
    args = parser.parse_args(argv)
    import pilot_freeze
    cases = args.cases or list(pilot_freeze.accepted_variants())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    results, started = [], time.monotonic()
    for case in cases:
        with tempfile.TemporaryDirectory(prefix="sentinel_") as workdir:
            result = walk(case, workdir)
        for row in result["english"]:
            row["pending"] = pending_item(row["line"], row["english"])
        results.append(result)
        unintended = sum(1 for row in result["english"] if not row["pending"])
        print(f"{case}: {len(result['english'])} lines with English ({unintended} unintended, "
              f"{len(result['english']) - unintended} pending faculty wording); stopped: {len(result['stopped'])}",
              flush=True)
    report = {"seconds": round(time.monotonic() - started), "cases": results,
              "pending_outside_the_walk": PENDING_OUTSIDE_THE_WALK}
    (out / "sentinel.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(len(r["english"]) for r in results)
    unintended = sum(1 for r in results for row in r["english"] if not row["pending"])
    stopped = sum(len(r["stopped"]) for r in results)
    print(f"{len(results)} cases; {total} lines with English: {unintended} unintended, {total - unintended} pending "
          f"faculty wording; {stopped} stopped steps; {report['seconds']} s")
    if PENDING_OUTSIDE_THE_WALK:
        print("Pending faculty wording outside the walk: " + ", ".join(sorted(PENDING_OUTSIDE_THE_WALK)))
    return 0 if not total and not stopped and not PENDING_OUTSIDE_THE_WALK else 1


if __name__ == "__main__":
    sys.exit(main())
