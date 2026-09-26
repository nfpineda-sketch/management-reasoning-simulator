"""The image bank from a terminal: the pilot plan, its batches, the inventory, the pack, the ledger.

    python tools_image_bank.py plan
    python tools_image_bank.py run --database-url URL --batch 1 --proxy-credentials
    python tools_image_bank.py inventory --database-url URL
    python tools_image_bank.py ledger --database-url URL
    python tools_image_bank.py export --database-url URL [--out assets/patient_images]
    python tools_image_bank.py import --database-url URL [--pack assets/patient_images]
    python tools_image_bank.py show --database-url URL --asset ID --out file.webp

``run`` makes paid requests, one job at a time, through the same broker and the
same budget the application uses: nothing starts that the budget's worst case
cannot cover, and the ledger records every request, retry and failure. It
refuses a database that is not the one the budget lives in: pass the database
whose ledger you want charged. ``--proxy-credentials`` is for an environment
whose network proxy adds the provider's credential itself; the key is then
never in this process. Without it the key is read from OPENAI_API_KEY.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

REQUESTED_BY = "agente:piloto-imagenes (ejecución sintética por un agente)"


def _bank(url):
    from account_store import AccountStore
    from image_bank import ImageBank
    return ImageBank(AccountStore(url, allow_sqlite=url.startswith("sqlite")))


def _budget():
    from image_pricing import configured_budget
    return configured_budget(lambda name: os.environ.get(name, ""))


def _usd(micro):
    from image_pricing import usd
    return f"US${usd(micro):.4f}"


def plan(args):
    import image_broker
    import image_pilot
    from clinical_cases import FAMILIES
    from image_identities import compatible, describe, identity
    from image_pricing import ceiling
    cases = {v["id"]: v for family in FAMILIES.values() for v in family["variants"]}
    bank = _bank(args.database_url) if args.database_url else None
    anchors = set()
    for item in image_pilot.items(args.batch):
        person = identity(item["identity"])
        contract = image_pilot.contract(item)
        fits = compatible(person, cases[item["case"]]["patient"])
        from image_bank import contract_key
        ready = bank is not None and bank.usable_asset(person["id"], contract_key(contract)) is not None
        needs_anchor = person["id"] not in anchors and (
            bank is None or bank.usable_asset(person["id"], image_broker.ANCHOR_KEY) is None)
        anchors.add(person["id"])
        worst = sum(ceiling(m, k) for k, m in (
            ([("create", "gpt-image-1.5"), ("screen", "gpt-5-mini"), ("repair", "gpt-image-1.5"),
              ("screen", "gpt-5-mini")] if needs_anchor else []) +
            [("edit", "gpt-image-1.5"), ("screen", "gpt-5-mini"), ("repair", "gpt-image-1.5"),
             ("screen", "gpt-5-mini")]))
        print(f"batch {item['batch']} · {person['id']} ({describe(person)}) · case {item['case']} "
              f"({'compatible' if fits else 'NOT COMPATIBLE'}) · {item['state']} · "
              f"{'ready' if ready else 'to make'} · worst case {_usd(worst)}"
              f"{' with its anchor' if needs_anchor else ''}")


def run(args):
    import image_broker
    import image_pilot
    from image_identities import identity
    bank = _bank(args.database_url)
    budget = _budget()
    api_key = "injected-by-environment-proxy" if args.proxy_credentials else os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        sys.exit("No credential: pass --proxy-credentials or set OPENAI_API_KEY.")
    print("budget before:", json.dumps(_summary(bank.budget_summary(budget))))
    for item in image_pilot.items(args.batch):
        if args.only and item["state"] != args.only:
            continue
        person = identity(item["identity"])
        contract = image_pilot.contract(item)
        started = time.monotonic()
        outcome, stalled = None, False
        for attempt in range(3):   # a new person's anchor first, then the state
            # ``--force`` lifts a failed state's pause for this one request only. Every
            # later request of the loop waits on a job, it never repeats a failed one:
            # four forced rounds once made four equivalent paid attempts (2026-09-26).
            outcome = image_broker.request(bank, person, contract, api_key=api_key, allowed=True,
                                           image_model=args.image_model, review_model=args.review_model,
                                           requested_by=REQUESTED_BY, budget=budget,
                                           force=args.force and attempt == 0)
            if outcome.state != "pending":
                break
            if attempt and outcome.stage not in ("ANCHOR", "QUEUED", "ELSEWHERE"):
                break
            try:
                image_broker.wait(timeout=900)
            except TimeoutError:
                stalled = True
                break
        if stalled:
            print("still running after 15 minutes; stopping here")
            break
        seconds = round(time.monotonic() - started, 1)
        asset = outcome.asset or {}
        print(f"{person['id']} · {item['state']} · {outcome.state} {outcome.code} {outcome.stage} · "
              f"{seconds}s · asset {asset.get('id', '-')} · screen {asset.get('screen', '-')}"
              f" · repaired {asset.get('generation', {}).get('repaired', '-')}")
        if outcome.state == "unavailable" and outcome.code.startswith("BUDGET"):
            print("the budget cannot cover the next job; stopping")
            break
    print("budget after:", json.dumps(_summary(bank.budget_summary(budget))))


def _summary(summary):
    from image_pricing import usd
    return {"budget": summary["budget_id"], "committed_usd": usd(summary["committed"]),
            "from_provider_usage_usd": usd(summary["from_usage"]), "estimated_usd": usd(summary["estimated"]),
            "in_flight_usd": usd(summary["in_flight"]), "remaining_usd": usd(summary["remaining_micro"]),
            "image_requests": summary["requests"], "remaining_requests": summary["remaining_requests"],
            "calls_sent": summary["calls_sent"], "retries": summary["retries"]}


def inventory(args):
    from image_identities import describe, identity
    bank = _bank(args.database_url)
    for asset in sorted(bank.assets(), key=lambda a: (a["identity_id"], a["created_at"])):
        facts = bank.blob_facts(asset["display_sha256"])
        print(f"{asset['id'][:10]} · {asset['identity_id']} · {asset['role']} · {asset['screen']}"
              f"{' (excluded: ' + asset['exclusion_reason'] + ')' if asset['excluded'] else ''} · "
              f"visual {asset['visual_review']} · clinical {asset['clinical_review']} · "
              f"{json.dumps(asset['contract'], sort_keys=True)} · display {facts['size_bytes']} bytes")


def ledger(args):
    from image_pricing import usd
    bank = _bank(args.database_url)
    budget = _budget()
    print(json.dumps(_summary(bank.budget_summary(budget)), indent=1))
    for row in bank.ledger(budget["id"]):
        print(f"{row['seq']:>3} {row['kind']:<6} {row['model']:<13} {row['status']:<9} "
              f"reserved {usd(row['reserved_micro']):.4f} cost {'' if row['cost_micro'] is None else usd(row['cost_micro'])} "
              f"({row['cost_basis']}) {row['error_code']} {'retry' if row['retry_of'] else ''}")


def export(args):
    import image_pack
    bank = _bank(args.database_url)
    manifest = image_pack.export_pack(bank, Path(args.out), budget=_budget())
    print(f"{len(manifest['assets'])} assets, {len(manifest['ledger'])} ledger rows written to {args.out}")


def import_(args):
    import image_pack
    print(json.dumps(image_pack.import_pack(_bank(args.database_url), Path(args.pack))))


def show(args):
    bank = _bank(args.database_url)
    asset = bank.asset(args.asset) or next((a for a in bank.assets() if a["id"].startswith(args.asset)), None)
    if asset is None:
        sys.exit("No such asset.")
    Path(args.out).write_bytes(bank.blob(asset["display_sha256"]))
    print(args.out)


def withdraw(args):
    bank = _bank(args.database_url)
    asset = bank.asset(args.asset) or next((a for a in bank.assets() if a["id"].startswith(args.asset)), None)
    if asset is None:
        sys.exit("No such asset.")
    for identifier in bank.withdraw(asset["id"], args.reason, by=REQUESTED_BY.split(" ")[0]):
        print("withdrawn", identifier)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "run", "inventory", "ledger", "export", "import", "show", "withdraw"):
        command = commands.add_parser(name)
        command.add_argument("--database-url", required=name != "plan", default="")
        if name in ("plan", "run"):
            command.add_argument("--batch", type=int, default=None)
        if name == "run":
            command.add_argument("--proxy-credentials", action="store_true")
            command.add_argument("--image-model", default="gpt-image-1.5")
            command.add_argument("--review-model", default="gpt-5-mini")
            command.add_argument("--force", action="store_true", help="ask again for a state that is cooling down")
            command.add_argument("--only", default="", help="only this state of the batch")
        if name == "export":
            command.add_argument("--out", default=str(ROOT / "assets" / "patient_images"))
        if name == "import":
            command.add_argument("--pack", default=str(ROOT / "assets" / "patient_images"))
        if name == "show":
            command.add_argument("--asset", required=True)
            command.add_argument("--out", required=True)
        if name == "withdraw":
            command.add_argument("--asset", required=True)
            command.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    {"plan": plan, "run": run, "inventory": inventory, "ledger": ledger, "export": export,
     "import": import_, "show": show, "withdraw": withdraw}[args.command](args)


if __name__ == "__main__":
    main()
