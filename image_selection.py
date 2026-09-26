"""Which person an encounter shows, and which of that person's images a state may use.

Pure functions, no database and no provider (faculty request of 2026-09-26).

The order of priorities is the faculty's:

1. **Clinical compatibility first.** An identity must fit the case's age and
   sex; nothing here ever changes the case to fit a face. An image must show
   exactly the state the engine recorded -- the whole visible contract, devices
   included -- or it is not the current patient.
2. **Then novelty for this resident.** An identity the resident has not seen
   comes before one they have, and among those they have seen, the one seen
   longest ago. When every compatible identity has been seen the repetition is
   recorded as such (``bank_limited``): the bank is small, not the choice.
3. **Then what is already saved.** Between equally new identities, one whose
   image for the arrival state already exists is shown at once and costs
   nothing.
4. **Then balance.** An identity drawn less often in this family, and less
   often overall, comes first, so that no face becomes the face of one
   family, one outcome or one severity.

Ties are broken by a hash of the encounter, so the choice is reproducible and
not always the first entry of the list.
"""
from __future__ import annotations

import hashlib

REVIEW_RANK = {"approved": 0, "pending": 1}


def human_approved(asset):
    """Both reviews a person records, visual and clinical, approved."""
    return asset.get("visual_review") == "approved" and asset.get("clinical_review") == "approved"


def usable(asset):
    """An asset the room may show: made, readable, screened, not refused and not excluded.

    Faculty decision 5 (2026-09-26): a person's approved visual and clinical
    reviews enable a photograph the automated screen rejected. Only the
    screen's own exclusion is lifted that way; a person's or a withdrawal's
    never is, and a rejected review always keeps the photograph out.
    """
    from image_bank import SCREEN_EXCLUSION
    if asset is None or asset.get("technical_check") != "passed":
        return False
    if asset.get("visual_review") == "rejected" or asset.get("clinical_review") == "rejected":
        return False
    if asset.get("screen") not in ("accepted", "accepted_with_limitations") and not human_approved(asset):
        return False
    if asset.get("excluded"):
        return asset.get("exclusion_reason") == SCREEN_EXCLUSION and human_approved(asset)
    return True


def best_asset(assets):
    """Among usable assets of one person in one state: reviewed first, then the newest."""
    candidates = [asset for asset in assets if usable(asset)]
    if not candidates:
        return None
    return sorted(candidates, key=lambda a: (REVIEW_RANK.get(a.get("clinical_review"), 2),
                                            REVIEW_RANK.get(a.get("visual_review"), 2),
                                            -int(a.get("created_at") or 0), a.get("id") or ""))[0]


def _tie(seed, identity_id):
    return hashlib.sha256(f"{seed}:{identity_id}".encode("utf-8")).hexdigest()


def choose_identity(candidates, *, exposures=None, usage=None, ready=frozenset(), family="", seed=""):
    """Choose among compatible identities; returns (identity, record of why).

    ``exposures``: {identity_id: {"last_shown": epoch, "encounters": n}} for
    this resident. ``usage``: {identity_id: {"total": n, "families": {...}}}.
    ``ready``: identities whose arrival-state image already exists.
    Returns (None, record) when no identity is compatible: the room then shows
    its neutral view and says why, and the case is left as it is.
    """
    exposures = exposures or {}
    usage = usage or {}
    if not candidates:
        return None, {"reason": "no_compatible_identity", "candidates": [], "repeat_kind": "none"}

    def rank(identity):
        seen = exposures.get(identity["id"])
        drawn = usage.get(identity["id"]) or {}
        return (1 if seen else 0,
                int(seen["last_shown"]) if seen else 0,
                0 if identity["id"] in ready else 1,
                int((drawn.get("families") or {}).get(family, 0)),
                int(drawn.get("total", 0)),
                _tie(seed, identity["id"]))

    ordered = sorted(candidates, key=rank)
    chosen = ordered[0]
    repeat_kind = "bank_limited" if chosen["id"] in exposures else "none"
    return chosen, {
        "reason": "unseen" if repeat_kind == "none" else "all_compatible_seen",
        "repeat_kind": repeat_kind,
        "candidates": [identity["id"] for identity in ordered],
        "ready": sorted(identity["id"] for identity in candidates if identity["id"] in ready),
        "seen": sorted(identity["id"] for identity in candidates if identity["id"] in exposures),
    }
