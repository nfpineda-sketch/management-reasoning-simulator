"""The photograph a resident agrees to store, and the agreement that allows it.

Faculty request of 2026-09-23: assessment happens at a distance, and a face
beside the initials and the training year helps a reviewer hold one encounter
apart from another. That is a reason, and it is also the first identifiable
personal data this application has ever stored, so it does not arrive quietly:

* **Nothing is stored without a signed agreement.** ``save_photo`` refuses
  unless the current agreement version has been accepted by that person. A new
  agreement version needs accepting again.
* **It is shown in one place only** -- the centre of the rubric radar -- and to
  two kinds of reader: the resident it belongs to, and faculty. A resident
  never reads another resident's anything, which the store enforces here as it
  does everywhere else.
* **The file is re-encoded, never kept.** What arrives is decoded, downscaled
  to a square thumbnail and written out as a fresh JPEG. Nothing of the
  original survives, including the EXIF block, which on a phone photograph
  routinely carries the place and moment it was taken.
* **It can be removed.** ``forget`` deletes the photograph and the initials and
  leaves the agreement record, because the fact that someone agreed, and when,
  is what makes the storage accountable.

The agreement text below is a **draft for the programme to replace**. It states
what the software actually does, which is the part I can be sure of; what it
cannot state is the institution's own retention, jurisdiction or contact.
"""

import base64
import io
import time
import uuid

from account_store import AccountError


AGREEMENT_VERSION = "1.0-pilot"
STAFF = frozenset({"faculty", "admin"})

# Square, small, and large enough to recognise a face at the centre of a chart.
THUMBNAIL = 256
MAX_UPLOAD_BYTES = 4 * 1024 * 1024
MAX_STORED_BYTES = 200 * 1024
MAX_INITIALS = 4

AGREEMENT = """\
**Draft for the programme to complete before the pilot runs with real residents.**

You are being asked to store a photograph of your face and your initials in this training
simulator.

**What is stored.** A photograph you choose, re-encoded by this application as a small square
image, together with initials you type and the training year your programme recorded. The
original file is not kept, and the information cameras attach to a photograph -- including the
place and the moment it was taken -- is discarded in that re-encoding.

**Why.** Encounters in this programme are reviewed at a distance. A face beside your initials
and your year helps a faculty member keep one encounter apart from another while reviewing it.

**Who can see it.** You, and faculty of this programme. It appears in one place: the centre of
your management reasoning profile chart, and on the assessment documents that carry that chart.
No other resident can see your photograph, your initials, your encounters, your scores or your
chart.

**What it is never used for.** It is not used to identify you to anyone outside this programme,
it is not shared, it is not published, and it takes no part in any score or decision about you.

**Withdrawing.** You can delete the photograph and the initials at any time from your account,
without giving a reason and without affecting your record or your standing in the programme.

**Not covered here.** How long your programme keeps your record, where its database is hosted,
and who to contact about your data are the programme's to state, and this text does not state
them.
"""


def initials_of(value):
    """Up to four letters, upper case, or "" when nothing usable was typed.

    "NP" stays "NP", and a name typed into the field becomes the initials of
    its words rather than its first four letters -- somebody will type their
    name there, and "NICO" is not what they meant.
    """
    words = [word for word in str(value or "").replace(".", " ").split() if word]
    letters = ("".join(word[0] for word in words if word[0].isalpha()) if len(words) > 1
               else "".join(c for c in (words[0] if words else "") if c.isalpha()))
    return letters[:MAX_INITIALS].upper()


def normalise(data):
    """A fresh square JPEG thumbnail, with nothing of the original inside it.

    Re-encoding is what removes the EXIF block, so this is a privacy step and
    not only a size one. A file that is not an image raises.
    """
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise AccountError("Choose an image file.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise AccountError("That image is too large. Choose one under 4 MB.")
    try:
        from PIL import Image
        with Image.open(io.BytesIO(bytes(data))) as opened:
            opened.load()
            image = opened.convert("RGB")
    except Exception:
        raise AccountError("That file could not be read as an image.") from None
    width, height = image.size
    side = min(width, height)
    left, top = (width - side) // 2, (height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((THUMBNAIL, THUMBNAIL))
    buffer = io.BytesIO()
    # A new file from decoded pixels: no EXIF, no colour profile, no comment.
    image.save(buffer, format="JPEG", quality=82, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    if len(encoded) > MAX_STORED_BYTES:
        raise AccountError("That image could not be reduced enough to store.")
    return encoded


def data_uri(encoded):
    return f"data:image/jpeg;base64,{encoded}" if encoded else ""


class ProfileStore:
    """The agreement, the initials and the photograph, kept beside the account."""

    def __init__(self, account_store):
        self.accounts = account_store
        self._execute = account_store._execute
        self._initialize()

    def _initialize(self):
        if self.accounts.schema_ready("resident_profile"):
            return
        statements = [
            """CREATE TABLE IF NOT EXISTS mrs_resident_agreements (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES mrs_users(id),
                agreement_version TEXT NOT NULL,
                accepted_at BIGINT NOT NULL
            )""",
            """CREATE INDEX IF NOT EXISTS mrs_resident_agreements_user
                ON mrs_resident_agreements(user_id, agreement_version)""",
            # Asked once, and what they chose. Separate from the acceptance
            # record above because a decline is not an acceptance and must
            # still stop the question from being asked again.
            """CREATE TABLE IF NOT EXISTS mrs_resident_setup (
                user_id TEXT PRIMARY KEY REFERENCES mrs_users(id),
                agreement_version TEXT NOT NULL,
                decision TEXT NOT NULL CHECK (decision IN ('accepted', 'declined')),
                decided_at BIGINT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_resident_profiles (
                user_id TEXT PRIMARY KEY REFERENCES mrs_users(id),
                initials TEXT NOT NULL DEFAULT '',
                photo_base64 TEXT,
                agreement_version TEXT NOT NULL,
                updated_at BIGINT NOT NULL
            )""",
        ]
        with self.accounts._transaction(write=True) as connection:
            for statement in statements:
                self._execute(connection, statement)
        self.accounts.mark_schema_ready("resident_profile")

    def _target(self, connection, token, user_id):
        """Whose profile this is about, and whether the reader may have it."""
        actor = self.accounts._actor(connection, token)
        if actor["role"] in STAFF:
            return actor, user_id or actor["id"]
        if user_id in (None, actor["id"]):
            return actor, actor["id"]
        raise AccountError("Your account does not have permission for this action.")

    def accepted(self, token, user_id=None, version=AGREEMENT_VERSION):
        """Whether this person has accepted that version of the agreement."""
        with self.accounts._transaction() as connection:
            _, target = self._target(connection, token, user_id)
            row = self._execute(connection, """SELECT accepted_at FROM mrs_resident_agreements
                WHERE user_id = ? AND agreement_version = ?
                ORDER BY accepted_at DESC LIMIT 1""", (target, version)).fetchone()
            return int(row["accepted_at"]) if row is not None else None

    def accept(self, token, version=AGREEMENT_VERSION):
        """Only for oneself. Nobody accepts an agreement on another's behalf."""
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token)
            self._execute(connection, "INSERT INTO mrs_resident_agreements VALUES (?, ?, ?, ?)",
                          (uuid.uuid4().hex, actor["id"], str(version), int(time.time())))
            self._decide(connection, actor["id"], "accepted", version)
            return actor["id"]

    def decline(self, token, version=AGREEMENT_VERSION):
        """Recorded so the question is asked once, and never asked again.

        A decline stores nothing about the person beyond the fact that they
        were asked and said no. It changes nothing else about their account:
        the whole point of an agreement is that refusing it costs nothing.
        """
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token)
            self._decide(connection, actor["id"], "declined", version)
            return actor["id"]

    def _decide(self, connection, user_id, decision, version):
        now = int(time.time())
        existing = self._execute(connection, "SELECT user_id FROM mrs_resident_setup "
                                 "WHERE user_id = ?", (user_id,)).fetchone()
        if existing is None:
            self._execute(connection, "INSERT INTO mrs_resident_setup VALUES (?, ?, ?, ?)",
                          (user_id, str(version), decision, now))
        else:
            self._execute(connection, """UPDATE mrs_resident_setup
                SET agreement_version = ?, decision = ?, decided_at = ? WHERE user_id = ?""",
                (str(version), decision, now, user_id))

    def decision(self, token, user_id=None, version=AGREEMENT_VERSION):
        """"accepted", "declined", or None when they have never been asked."""
        with self.accounts._transaction() as connection:
            _, target = self._target(connection, token, user_id)
            row = self._execute(connection, """SELECT decision FROM mrs_resident_setup
                WHERE user_id = ? AND agreement_version = ?""",
                (target, str(version))).fetchone()
            return row["decision"] if row is not None else None

    def get(self, token, user_id=None):
        """The initials and the photograph, or empty ones. Never another's."""
        with self.accounts._transaction() as connection:
            _, target = self._target(connection, token, user_id)
            row = self._execute(connection, """SELECT * FROM mrs_resident_profiles
                WHERE user_id = ?""", (target,)).fetchone()
            if row is None:
                return {"user_id": target, "initials": "", "photo": "",
                        "agreement_version": "", "updated_at": None}
            return {"user_id": target, "initials": row["initials"] or "",
                    "photo": row["photo_base64"] or "",
                    "agreement_version": row["agreement_version"],
                    "updated_at": row["updated_at"]}

    def save(self, token, *, initials=None, photo=None, version=AGREEMENT_VERSION):
        """Store one's own initials and photograph. Refused without the agreement.

        Only for oneself: a faculty member may read a resident's profile and
        may not write one.
        """
        encoded = None if photo is None else normalise(photo)
        clean = None if initials is None else initials_of(initials)
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token)
            signed = self._execute(connection, """SELECT id FROM mrs_resident_agreements
                WHERE user_id = ? AND agreement_version = ? LIMIT 1""",
                (actor["id"], str(version))).fetchone()
            if signed is None:
                raise AccountError(
                    "Accept the photograph and initials agreement before storing either.")
            row = self._execute(connection, "SELECT * FROM mrs_resident_profiles WHERE user_id = ?",
                                (actor["id"],)).fetchone()
            now = int(time.time())
            if row is None:
                self._execute(connection, "INSERT INTO mrs_resident_profiles VALUES (?, ?, ?, ?, ?)",
                              (actor["id"], clean or "", encoded, str(version), now))
            else:
                self._execute(connection, """UPDATE mrs_resident_profiles
                    SET initials = ?, photo_base64 = ?, agreement_version = ?, updated_at = ?
                    WHERE user_id = ?""",
                    (row["initials"] if clean is None else clean,
                     row["photo_base64"] if photo is None else encoded,
                     str(version), now, actor["id"]))
            return actor["id"]

    def forget(self, token):
        """Delete one's own photograph and initials; keep that one agreed.

        The agreement record stays because it is what makes the storage
        accountable: deleting it would erase the evidence that consent existed.
        """
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token)
            self._execute(connection, "DELETE FROM mrs_resident_profiles WHERE user_id = ?",
                          (actor["id"],))
            return actor["id"]


def badge(store, token, user_id, training_year=None):
    """What the centre of the chart shows, for a reader allowed to see it.

    Returns ``None`` rather than raising when the reader is not allowed, so a
    chart still draws for somebody who may see the scores and not the face.
    """
    try:
        profile = ProfileStore(store).get(token, user_id)
    except AccountError:
        return None
    if not (profile["photo"] or profile["initials"]):
        return None
    return {"image": data_uri(profile["photo"]), "initials": profile["initials"],
            "year": training_year}
