"""The bank's images as files in the repository, and back into a database (2026-09-26).

The first real images were made from an environment that reaches the provider
but not the development database. They travel as a pack: every asset with its
provenance, the images themselves, the jobs and the ledger of what they cost.
The application imports the pack into its own database the first time a
process opens the bank, once per pack; an asset or a ledger row already there
is never overwritten, so a review recorded in the database survives a later
import. The pack is also a second, versioned copy of the bank, which no server
restart or expired provider link can take away.

Only the browser copy of each image travels (WebP), plus a larger reference
copy of each accepted anchor, the photograph later states are edited from. The
provider's original PNG is not stored in the repository: its SHA-256 and size
are, as provenance.
"""
from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path

PACK_VERSION = 1
PACK_DIR = Path(__file__).resolve().parent / "assets" / "patient_images"
MANIFEST = "manifest.json"
# Reviews a person gave outside the application's database, each under the
# account it names (faculty, 2026-09-26: the pilot's photographs approved in the
# chat). Written by hand or by the tool, never by an export.
APPROVALS = "approvals.json"


def _webp(raw, quality):
    from PIL import Image
    with Image.open(BytesIO(raw)) as image:
        output = BytesIO()
        image.convert("RGB").save(output, format="WEBP", quality=quality, method=6)
    return output.getvalue()


def _write(directory, raw, suffix=".webp"):
    sha = hashlib.sha256(raw).hexdigest()
    path = directory / f"{sha}{suffix}"
    if not path.exists():
        path.write_bytes(raw)
    return {"file": path.name, "sha256": sha, "size": len(raw)}


def export_pack(bank, directory=PACK_DIR, *, budget):
    """Write every asset, job and ledger row of ``budget`` to ``directory``; returns the manifest."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    assets = []
    for asset in sorted(bank.assets(), key=lambda a: (a["created_at"], a["id"])):
        display = bank.blob(asset["display_sha256"])
        entry = {key: asset[key] for key in (
            "id", "identity_id", "identity_version", "kind", "role", "state_key", "contract", "devices",
            "reference_asset_id", "generation", "origin", "technical_check", "screen", "screen_details",
            "visual_review", "clinical_review", "excluded", "exclusion_reason", "created_at")}
        entry["display"] = _write(directory, display)
        master = bank.blob(asset["master_sha256"]) if asset.get("master_sha256") else None
        entry["provider_original"] = ({"sha256": asset["master_sha256"], "size": len(master),
                                       "content_type": bank.blob_facts(asset["master_sha256"])["content_type"]}
                                      if master is not None else None)
        # The photograph later states are edited from, kept sharper than the browser copy.
        entry["reference"] = (_write(directory, _webp(master, 92))
                              if master is not None and asset["role"] == "anchor"
                              and asset["screen"] in ("accepted", "accepted_with_limitations") else None)
        assets.append(entry)
    limits = ("id", "limit_micro", "limit_requests", "authorization")
    # Every budget the bank has spent from travels with its ledger: a later
    # authorization never drops the record of an earlier one.
    budgets = {entry["id"]: entry for entry in bank.budgets()}
    budgets.setdefault(budget["id"], budget)
    manifest = {"pack_version": PACK_VERSION, "budget": {key: budget[key] for key in limits},
                "assets": assets, "jobs": sorted(bank.jobs(limit=10000), key=lambda j: (j["finished_at"], j["id"])),
                "ledger": bank.ledger(budget["id"], limit=10000),
                "ledgers": [{"budget": {key: entry[key] for key in limits}, "rows": bank.ledger(entry["id"], limit=10000)}
                            for entry in budgets.values()]}
    (directory / MANIFEST).write_text(json.dumps(manifest, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                      encoding="utf-8")
    return manifest


def read_manifest(directory=PACK_DIR):
    path = Path(directory) / MANIFEST
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def import_pack(bank, directory=PACK_DIR):
    """Bring a pack into this database. Returns what was added; nothing already there changes."""
    directory = Path(directory)
    manifest = read_manifest(directory)
    if manifest is None:
        return {"assets": 0, "ledger": 0, "jobs": 0}
    if manifest.get("pack_version") != PACK_VERSION:
        raise ValueError("This image pack was written by another version.")
    known = bank.known_assets()
    added = 0
    for entry in manifest["assets"]:
        if entry["id"] in known:
            continue
        display = _read(directory, entry["display"])
        reference = _read(directory, entry["reference"]) if entry.get("reference") else None
        display_sha = bank.put_blob(display)
        master_sha = bank.put_blob(reference) if reference is not None else None
        bank.add_asset(asset_id=entry["id"], identity_id=entry["identity_id"],
                       identity_version=entry["identity_version"], role=entry["role"], contract=entry["contract"],
                       devices=entry["devices"], display_sha256=display_sha, master_sha256=master_sha,
                       reference_asset_id=entry.get("reference_asset_id"),
                       generation={**entry["generation"], "imported_from_pack": True,
                                   "provider_original": entry.get("provider_original")},
                       screen=entry["screen"], screen_details=entry.get("screen_details") or {},
                       origin=entry["origin"], technical_check=entry["technical_check"], kind=entry["kind"],
                       excluded=bool(entry["excluded"]), exclusion_reason=entry.get("exclusion_reason") or "",
                       created_at=entry["created_at"], visual_review=entry.get("visual_review", "pending"),
                       clinical_review=entry.get("clinical_review", "pending"))
        added += 1
    ledgers = manifest.get("ledgers") or [{"budget": manifest["budget"], "rows": manifest.get("ledger") or []}]
    ledger = sum(bank.import_ledger(entry["budget"], entry["rows"]) for entry in ledgers)
    jobs = sum(1 for job in manifest.get("jobs") or [] if bank.import_job(job))
    approvals = {}
    for entry in read_approvals(directory):
        outcome = bank.import_approval(entry)
        approvals[outcome] = approvals.get(outcome, 0) + 1
    return {"assets": added, "ledger": ledger, "jobs": jobs, "approvals": approvals}


def read_approvals(directory=PACK_DIR):
    path = Path(directory) / APPROVALS
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _read(directory, record):
    raw = (Path(directory) / record["file"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != record["sha256"]:
        raise ValueError(f"The pack file {record['file']} does not match its manifest.")
    return raw


def ensure_imported(bank, directory=None):
    """Import the repository's pack once per process and database; quietly nothing without one."""
    directory = Path(directory) if directory is not None else PACK_DIR
    path = directory / MANIFEST
    if not path.exists():
        return None
    approvals = directory / APPROVALS
    digest = hashlib.sha256(path.read_bytes() + (approvals.read_bytes() if approvals.exists() else b"")
                            ).hexdigest()[:16]
    marker = f"image_pack:{digest}"
    if bank.accounts.schema_ready(marker):
        return None
    result = import_pack(bank, directory)
    bank.accounts.mark_schema_ready(marker)
    return result
