"""Pre-Phase1 governance: the order reader is frozen at the accepted post-V3 state."""

from hashlib import sha1
from pathlib import Path


# Git blob SHAs of the five reader files accepted for the pre-Phase1 freeze.
# family_parser.py includes the four reviewed 2026-10-11 reader corrections.
# The other four remain byte-identical to the V3 freeze.
EXPECTED_BLOBS = {
    "family_parser.py": "1d17bf8b3dce66da5f1c8291237e2e7a7afde1c0",
    "shared_order_language.py": "5ed6a8a14aa2f7cf077ffaf2a202ee9cf0bd8047",
    "shared_order_quantities.py": "65e3606a2fd80bc6fb1f988e48460e6b2f6f100c",
    "active_order_context.py": "3c0432f5711cfbd3a919649e1bbe52cce3afbaeb",
    "weight_based_doses.py": "cdf79e0e654e11f908a90eb91139c9812a2416e8",
}


def _git_blob_sha(path):
    data = Path(path).read_bytes()
    return sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def test_prephase1_reader_freeze_is_exact():
    assert {path: _git_blob_sha(path) for path in EXPECTED_BLOBS} == EXPECTED_BLOBS
