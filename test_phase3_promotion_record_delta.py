"""FD-PROMOTE-01 (declared adaptation): how the committed, code-derived checkpoint records stay HISTORICAL after the promotion.

TEST-SIDE. Several committed records under ``docs/revision`` are built from the code (``build_record()``), and their tests said "the committed record is what the code says now; regenerate it deliberately". Two
of those records are also PINNED by digest in later records (the P3-300 faculty-review checkpoint is byte-identical-checked by four independent tests, and it embeds the digests of the turn checkpoint and of the
pressure-authority series), so a regeneration would break the very chain that proves the history was not rewritten. The promotion therefore regenerates NONE of them.

What changed in the code, and therefore the ONLY difference between each stored record and what its builder returns today, is the list of approved authority snapshots: it now holds the promoted
``GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1`` beside ``gi_pressure_committed`` (FD-PROMOTE-01). ``delta_problems`` accepts exactly that difference and refuses every other one, so each of those tests still pins
everything it pinned before (every other field, byte for byte), and a stored record must still be self-sealed (its digest re-derives from its own body: it was not edited).
"""
import copy

import runtime_authority as ra

PROMOTED = "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1"
OLDER = "gi_pressure_committed"


def _get(record, path):
    node = record
    for key in path:
        node = node[key]
    return node


def _set(record, path, value):
    node = record
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value


def delta_problems(stored, live, *, path=("from_the_code", "approved_authority_snapshots")):
    """Every reason ``live`` is not ``stored`` plus the one declared promotion delta at ``path`` (an empty list: it is). Never raises on a well-formed record."""
    problems = []
    body = {key: value for key, value in stored.items() if key != "record_digest"}
    if stored.get("record_digest") != ra.digest_of(body):
        problems.append("the stored record is not self-sealed: it was edited")
    live_body = {key: value for key, value in live.items() if key != "record_digest"}
    if live.get("record_digest") != ra.digest_of(live_body):
        problems.append("the live record is not self-sealed")
    expected = copy.deepcopy(body)
    historical = list(_get(expected, path))
    if PROMOTED in historical:
        problems.append("the stored record already names the promoted snapshot: it is not a historical record")
    _set(expected, path, sorted([*historical, PROMOTED]))
    if live_body != expected:
        problems.append("the live record differs from the stored one by more than the declared promotion delta")
    return problems


def same_but_for_the_promotion(stored, live, **kwargs):
    return not delta_problems(stored, live, **kwargs)


# -- the helper's own proof: it accepts the one declared difference and refuses everything else -----------------------------------------------------------------------------------------------------

def _record(**changes):
    body = {"record_type": "X", "from_the_code": {"approved_authority_snapshots": [OLDER], "other": [1, 2]}, "authority": {"granted": False}}
    body.update(changes)
    return {**body, "record_digest": ra.digest_of(body)}


def test_d1_the_declared_delta_is_accepted():
    stored = _record()
    body = {"record_type": "X", "from_the_code": {"approved_authority_snapshots": sorted([OLDER, PROMOTED]), "other": [1, 2]}, "authority": {"granted": False}}
    live = {**body, "record_digest": ra.digest_of(body)}
    assert delta_problems(stored, live) == [] and same_but_for_the_promotion(stored, live)


def test_d2_every_other_difference_is_refused():
    stored = _record()

    def live_with(**changes):
        body = {"record_type": "X", "from_the_code": {"approved_authority_snapshots": sorted([OLDER, PROMOTED]), "other": [1, 2]}, "authority": {"granted": False}}
        body.update(changes)
        return {**body, "record_digest": ra.digest_of(body)}
    assert delta_problems(stored, _record()), "no promotion at all is not the declared delta either"
    assert delta_problems(stored, live_with(authority={"granted": True})), "an authority field changed"
    assert delta_problems(stored, live_with(from_the_code={"approved_authority_snapshots": sorted([OLDER, PROMOTED]), "other": [1, 2, 3]})), "another field of the same block changed"
    assert delta_problems(stored, live_with(from_the_code={"approved_authority_snapshots": sorted([OLDER, PROMOTED, "LOW"]), "other": [1, 2]})), "one more approved snapshot than the promotion"
    assert delta_problems(stored, live_with(extra=1)), "a new field"
    edited = {**copy.deepcopy(stored), "authority": {"granted": True}}                                 # an edited stored record keeps the old digest
    assert delta_problems(edited, live_with()), "a stored record that is not self-sealed"
    already = _record(from_the_code={"approved_authority_snapshots": sorted([OLDER, PROMOTED]), "other": [1, 2]})
    assert delta_problems(already, live_with()), "a record that already names the promoted snapshot is not a historical one"
