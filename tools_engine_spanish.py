"""The engine's sentences a Spanish reader still sees in English, found by playing (cycle 10, C10-08).

DF-23 row 11 left one part open: the sentences the engine composes -- a wall's
motion, an examination finding, a clinical update -- that ``language.say``
leaves in English, or half in English ("mildly reducido contraction"). This
tool finds them by playing the room, not by guessing at the code:

``--harvest DIR``
    Plays the twenty rehearsal scripts (``tanda20``, orders in Spanish) and a
    short probe of the eleven bank cases they do not cover, offline, through the
    real page (``tools_tanda20``), and writes ``DIR/events.json``: every entry
    the room showed, stored in English as every record is, with its case.

``--inventory EVENTS OUT``
    Reads that file and writes the templates that still show English once
    presented in Spanish (numbers written ``{n}``), with how often and where.

A case's own narrative is left out: it has its own approval, case by case
(``case_text``), and stays English until the faculty approves it. The
resident's own words are left out too: they are quoted, never translated.

Nothing here translates or approves anything, and nothing calls a provider.
The Spanish drafts are in ``engine_phrases_es``, inactive until the faculty
approves them (packet R-4).
"""
import os
import sys

if __name__ == "__main__":
    # The harvest must never reach a provider, whatever the environment has.
    os.environ["MRS_OFFLINE_CASES"] = "1"

import argparse
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

#: Words that never occur in the Spanish of the room. A drug name, a unit and an
#: abbreviation are the same in both languages (``language``), so none is here.
ENGLISH_ONLY = frozenset("""
the and with after of is are was were has have had this that these those it its they their from for
by at on to into over than then while without within shows show showing remains still now not your
you please which when where what patient minutes hours given started stopped reduced normally mildly
moderately severely mild moderate severe contraction contract contracts wall walls left right below
above yet been being be will would should can could may might must do does did an as or if no longer
""".split()) - {"no"}

#: The kinds the resident wrote, or that quote what they wrote.
RESIDENT_KINDS = frozenset({"you", "reasoning_completion"})
APP = ROOT / "app.py"

#: The eleven bank cases the twenty scripts do not play, with a challenge they launch under.
PROBE_CASES = (
    ("acs_52m_de_winter", "R2-02"), ("acs_61m_posterior", "R2-02"), ("acs_70f_left_main", "R2-02"),
    ("bradycardia_avb3_78f", "R2-04"), ("bradycardia_bb_54f", "R2-04"), ("bradycardia_hyperk_63m", "R2-04"),
    ("hypoglycemia_54m_thiamine", "R1-06"), ("obstructive_pyelonephritis_58f", "R2-05"),
    ("pulmonary_edema_75f", "R1-05"), ("trauma_hemothorax_41m", "R2-05"), ("trauma_limb_hemorrhage_27m", "R2-05"),
)
#: What the probe orders after examining: studies, then time for their results.
PROBE_ORDERS = (
    "Solicito ECG de 12 derivaciones, radiografía de tórax, gases venosos, hemograma, electrolitos, "
    "glicemia capilar y ecografía a pie de cama.",
    "Reevalúo en 30 minutos.",
)


def residue(text):
    """The English-only words a Spanish reader would see in this presented text."""
    quoted = re.sub(r"«[^»]*»", " ", str(text or ""))
    # Whole words, accents included: "así" is not "as".
    return sorted({word for word in re.findall(r"[^\W\d_]+(?:-[^\W\d_]+)?", quoted)
                   if word.lower() in ENGLISH_ONLY})


def still_english(said, english):
    """Whether a presented text still shows English: an English-only word, or the English left as it was."""
    unchanged = str(said or "").strip() == str(english or "").strip()
    return bool(residue(said)) or (unchanged and len(re.findall(r"[^\W\d_]+", str(english or ""))) >= 3)


def room_kinds():
    """How the room presents each kind of entry (``app.render_event``), read from app.py so it cannot drift."""
    import ast
    found = {}
    for node in ast.parse(APP.read_text(encoding="utf-8")).body:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and node.value.args
                and getattr(node.value.func, "id", "") == "frozenset"):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("_TRANSLATED_EVENTS", "_NARRATIVE_EVENTS"):
                    found[target.id] = frozenset(ast.literal_eval(node.value.args[0]))
    return found["_TRANSLATED_EVENTS"], found["_NARRATIVE_EVENTS"]


def template(text):
    """The sentence with its numbers and quoted words set aside, so one row stands for all."""
    text = re.sub(r"«[^»]*»", "«…»", str(text or ""))
    return re.sub(r"\d+(?:[.,]\d+)?", "{n}", text).strip()


def _narrative():
    """Every English passage a case's own narrative drafted for approval, longest first."""
    import case_text
    passages = {row["en"] for rows in case_text.passages("es").values() for row in rows.values()
                if isinstance(row, dict) and row.get("en")}
    return sorted(passages, key=len, reverse=True)


def presented(text, narrative=None, kind="clinical_update", kinds=None):
    """The Spanish reader's text, as the room presents this kind, with any case narrative taken out.

    The room says the engine's entries with ``language.say``, an examination with
    ``language.examination`` and the case's own words (presentation, history) only
    as the faculty approved them (``app.render_event``). The narrative is taken out
    because it has its own approval, case by case.
    """
    import language
    translated, told = kinds or room_kinds()
    text = str(text or "")
    if kind in translated:
        said = language.say(text, "es")
    elif kind == "examination":
        said = language.examination(text, "es")
    elif kind in told:
        said = language.case_words(text, "es")
    else:
        said = text
    for passage in narrative if narrative is not None else _narrative():
        if passage in said:
            said = said.replace(passage, " ")
    return said


def inventory(events, narrative=None):
    """The templates that still show English in Spanish: [{kind, english, spanish, residue, count, cases}]."""
    narrative = _narrative() if narrative is None else narrative
    kinds = room_kinds()
    rows = {}
    for event in events:
        if event.get("kind") in RESIDENT_KINDS:
            continue
        english = str(event.get("text") or "")
        said = presented(english, narrative, event.get("kind"), kinds)
        if not still_english(said, english):
            continue
        words = residue(said)
        key = (event.get("kind"), template(english))
        row = rows.setdefault(key, {"kind": event.get("kind"), "english": key[1], "example": english,
                                    "spanish": template(said), "residue": words, "count": 0, "cases": []})
        row["count"] += 1
        if event.get("case_id") and event["case_id"] not in row["cases"]:
            row["cases"].append(event["case_id"])
    return sorted(rows.values(), key=lambda row: (str(row["kind"]), row["english"]))


# --- the harvest -------------------------------------------------------------------

def _stored_events(url, case_id):
    """The events the room stored for the rehearsal's one encounter, in English."""
    from account_store import AccountStore
    store = AccountStore(url, allow_sqlite=True)
    admin = store.authenticate("ensayo_admin", "rehearsal-only-password")
    rows = []
    for attempt in store.list_attempts(admin):
        record = store.get_attempt(admin, attempt["id"])
        for event in ((record.get("payload") or {}).get("session") or {}).get("events") or []:
            if isinstance(event, dict):
                rows.append({"case_id": case_id, "kind": event.get("kind"), "text": str(event.get("text") or "")})
    return rows


def _probe(case_id, challenge, workdir, number):
    """Examine every offered area, order the studies, wait for them: what the room says, offline."""
    import tools_tanda20 as rehearsal
    from streamlit.testing.v1 import AppTest
    import curriculum_runtime
    from account_store import AccountStore, hash_password
    from resident_profile import ProfileStore
    url = f"sqlite:///{Path(workdir) / ('probe-%02d.sqlite3' % number)}"
    finding = {"case_id": case_id, "stopped": None}
    with rehearsal._environment({"MRS_AUTH_MODE": "accounts", "MRS_DATABASE_URL": url,
                                 "MRS_ALLOW_LOCAL_SQLITE": "true", "MRS_OFFLINE_CASES": "1",
                                 "MRS_DEFAULT_VARIANT": case_id,
                                 "MRS_SYNTHETIC_ACCOUNTS": rehearsal.TEST_ACCOUNT}):
        store = AccountStore(url, allow_sqlite=True)
        store.bootstrap_admin("ensayo_admin", hash_password("rehearsal-only-password"))
        admin = store.authenticate("ensayo_admin", "rehearsal-only-password")
        token = store.register(rehearsal.TEST_ACCOUNT, "rehearsal-only-resident",
                               store.create_invite(admin, "resident", 3))
        ProfileStore(store).decline(token)
        real = curriculum_runtime.assign_challenge
        curriculum_runtime.assign_challenge = lambda *args, **kwargs: {
            "challenge_id": challenge, "reason": "probe_pinned", "assignment_seed": 17,
            "competence_decision": "Not assessed automatically"}
        try:
            at = AppTest.from_file(rehearsal.APP, default_timeout=120)
            at.session_state["_account_token"] = token
            at.run()
            rehearsal._click(at, "Begin Encounter")
            drawn = ((at.session_state["state"] or {}).get("encounter_spec") or {}).get("variant_id")
            if drawn != case_id:
                raise rehearsal.RehearsalStop(f"The launch drew {drawn!r}, not {case_id!r}.")
            rehearsal._mode(at, "Examine")
            areas = list(next(item for item in at.selectbox if item.label == "Examine").options)
            for area in areas:
                rehearsal._step(at, ("examine", area))
            for order in PROBE_ORDERS:
                outcome = rehearsal._step(at, ("order", order))
                if outcome["held"]:
                    rehearsal._click(at, "Cancel pending orders")
            finding["areas"] = areas
        except rehearsal.RehearsalStop as stop:
            finding["stopped"] = str(stop)
        except Exception as error:  # the tool's own failure, reported as such
            finding["stopped"] = f"{type(error).__name__}: {error}"
        finally:
            curriculum_runtime.assign_challenge = real
    return finding, _stored_events(url, case_id)


def harvest(workdir):
    """Every entry the room showed in the twenty scripts and the eleven probes, in English."""
    import tanda20
    import tools_tanda20 as rehearsal
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    events, played = [], []
    for script in tanda20.SCRIPTS:
        result = rehearsal.rehearse(script, workdir)
        url = f"sqlite:///{workdir / ('rehearsal-%02d.sqlite3' % script['number'])}"
        events += _stored_events(url, script["case_id"])
        played.append({"script": script["number"], "case_id": script["case_id"], "stopped": result.get("stopped")})
    for number, (case_id, challenge) in enumerate(PROBE_CASES, 1):
        finding, found = _probe(case_id, challenge, workdir, number)
        events += found
        played.append({"probe": number, **finding})
    return {"played": played, "events": events}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--harvest", metavar="DIR")
    parser.add_argument("--inventory", nargs=2, metavar=("EVENTS", "OUT"))
    args = parser.parse_args(argv)
    if args.harvest:
        started = time.monotonic()
        found = harvest(args.harvest)
        found["seconds"] = round(time.monotonic() - started)
        Path(args.harvest, "events.json").write_text(json.dumps(found, indent=1, ensure_ascii=False),
                                                     encoding="utf-8")
        stopped = [row for row in found["played"] if row.get("stopped")]
        print(f"{len(found['events'])} entries from {len(found['played'])} runs; stopped: {len(stopped)}")
        for row in stopped:
            print("  stopped:", row)
    if args.inventory:
        events = json.loads(Path(args.inventory[0]).read_text(encoding="utf-8"))["events"]
        rows = inventory(events)
        Path(args.inventory[1]).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{len(rows)} templates still show English in Spanish")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
