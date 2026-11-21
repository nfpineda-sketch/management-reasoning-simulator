"""Pre-Phase1 governance: the order reader is frozen at the accepted state -- the post-V3 state, with TWO successors.

FD-TARGET-01 (2026-11-20) and FD-ORDER-01 to FD-ORDER-11 (2026-11-21): the faculty lifted the reader freeze twice, each time ONLY for one narrowly scoped safety correction (a physiologic target is never a drug rate;
a rate and a stop belong to one drug). ``family_parser.py`` is therefore pinned at its CURRENT successor blob below; the two blobs the freeze accepted before (``HISTORICAL_BLOBS``, the Phase-2 closure reader, and
``TARGET_SAFETY_BLOBS``, the first successor) are NOT forgotten: ``reader_succession`` rebuilds each, byte for byte, from the live file, and ``test_phase3_reader_succession.py`` proves it. The other four reader files
remain byte-identical to the V3 freeze. The reader is frozen again at the current successor: any further change is a new decision.
"""

from hashlib import sha1
from pathlib import Path


# Git blob SHAs of the five reader files accepted for the freeze. family_parser.py is the CURRENT SUCCESSOR (order-safety hardening, 2026-11-21, after the target-safety repair of 2026-11-20); it includes the four reviewed
# 2026-10-11 reader corrections.
# The other four remain byte-identical to the V3 freeze.
EXPECTED_BLOBS = {
    "family_parser.py": "a71a3888bc687a17a9eea24a6b06096ad58ae448",
    "shared_order_language.py": "5ed6a8a14aa2f7cf077ffaf2a202ee9cf0bd8047",
    "shared_order_quantities.py": "65e3606a2fd80bc6fb1f988e48460e6b2f6f100c",
    "active_order_context.py": "3c0432f5711cfbd3a919649e1bbe52cce3afbaeb",
    "weight_based_doses.py": "cdf79e0e654e11f908a90eb91139c9812a2416e8",
}
#: The reader the freeze accepted BEFORE the successors: still the reader of the Phase-2 closure and of the V3 baselines, and reconstructable (``reader_succession.historical_reader_bytes``).
HISTORICAL_BLOBS = {"family_parser.py": "1d17bf8b3dce66da5f1c8291237e2e7a7afde1c0"}
#: The FIRST successor (target-safety, 2026-11-20): the reader of the first successor record, reconstructable too (``reader_succession.target_safety_reader_bytes``).
TARGET_SAFETY_BLOBS = {"family_parser.py": "7a85714eb2b6fccb47507384a71fe91451e71ecb"}


def _git_blob_sha(path):
    data = Path(path).read_bytes()
    return sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def test_prephase1_reader_freeze_is_exact():
    assert {path: _git_blob_sha(path) for path in EXPECTED_BLOBS} == EXPECTED_BLOBS
