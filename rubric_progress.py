"""What a resident's confirmed assessments look like taken together.

A profile across encounters, not a grade. Everything here is read from reviews
a faculty member has **confirmed**: a draft is somebody's work in progress and
never reaches an average, and an encounter nobody has assessed is absent rather
than counted as a zero.

Two rules the arithmetic keeps, and they are the same two the single-encounter
chart keeps:

  * **A domain averages only over the encounters where it was assessable.**
    A case that offered no opportunity to observe continuity contributes
    nothing to continuity, in either direction. Each domain therefore carries
    its own count, and the count is shown.
  * **The penalty for a critical event is not averaged into a domain.** It is
    counted, and reported beside the profile, because a safety event is an
    event and not a fraction of one.

Nothing here talks to a model, a database or a screen.
"""

from rubric import DOMAIN_IDS, DOMAINS, MAX_DOMAIN_SCORE, NOT_ASSESSABLE


def _scores(review):
    scores = (review or {}).get("scores") or {}
    return {domain: value for domain, value in scores.items()
            if domain in DOMAIN_IDS and isinstance(value, int)
            and not isinstance(value, bool) and 0 <= value <= MAX_DOMAIN_SCORE}


def confirmed(reviews):
    """Only what a faculty member completed, oldest first."""
    kept = [review for review in reviews or [] if (review or {}).get("status") == "confirmed"]
    return sorted(kept, key=lambda review: (review.get("created_at") or 0,
                                            review.get("sequence") or 0))


def aggregate(reviews):
    """Per-domain mean, count and direction across the confirmed encounters."""
    history = confirmed(reviews)
    per_domain = {}
    for domain in DOMAIN_IDS:
        values = [_scores(review)[domain] for review in history if domain in _scores(review)]
        per_domain[domain] = {
            "domain_id": domain,
            "title": DOMAINS[domain]["title"],
            "title_es": DOMAINS[domain]["title_es"],
            "mean": round(sum(values) / len(values), 2) if values else None,
            "encounters": len(values),
            "latest": values[-1] if values else None,
            # The direction of the last step, not a trend line: two points are
            # not a trajectory and this does not pretend they are.
            "change": (values[-1] - values[-2]) if len(values) > 1 else None,
            "values": values,
        }
    events = sum(int((review.get("totals") or {}).get("critical_events") or 0)
                 for review in history)
    complete = [review for review in history
                if (review.get("totals") or {}).get("coverage", {}).get("complete")]
    adjusted = [int(review["totals"]["adjusted"]) for review in complete
                if isinstance(review.get("totals", {}).get("adjusted"), int)]
    return {
        "encounters": len(history),
        "complete_encounters": len(complete),
        "domains": per_domain,
        "critical_events": events,
        "mean_adjusted": round(sum(adjusted) / len(adjusted), 1) if adjusted else None,
        "maximum": len(DOMAIN_IDS) * MAX_DOMAIN_SCORE,
        "weakest": _weakest(per_domain),
        "rubric_versions": sorted({review.get("rubric_version", "") for review in history
                                   if review.get("rubric_version")}),
    }


def _weakest(per_domain):
    """The domain with the lowest mean, when there is one to name.

    A tie names nobody: "where more training is needed" is a claim, and a
    claim that two domains satisfy equally is not a direction.
    """
    scored = [row for row in per_domain.values() if row["mean"] is not None]
    if len(scored) < 2:
        return None
    lowest = min(row["mean"] for row in scored)
    candidates = [row["domain_id"] for row in scored if row["mean"] == lowest]
    return candidates[0] if len(candidates) == 1 else None


def average_series(summary, language="en", *, colour=None):
    """The running average, in the shape the radar draws.

    Returns ``None`` when there is nothing to average, so a first encounter
    shows its own shape alone rather than a second outline identical to it.
    """
    if not summary or summary["encounters"] < 2:
        return None
    values = {domain: row["mean"] for domain, row in summary["domains"].items()
              if row["mean"] is not None}
    if not values:
        return None
    label = (f"Promedio de {summary['encounters']} encuentros" if language == "es"
             else f"Average of {summary['encounters']} encounters")
    series = {"key": "average", "label": label, "values": values, "opacity": 0.09}
    if colour:
        series["colour"] = colour
    return series


def caption(summary, language="en"):
    """One line saying what the second outline is and what it rests on."""
    if not summary or summary["encounters"] < 2:
        return ""
    counts = sorted({row["encounters"] for row in summary["domains"].values()
                     if row["mean"] is not None})
    if language == "es":
        line = (f"Naranjo: el promedio de este residente en {summary['encounters']} "
                f"encuentros confirmados.")
        if counts and counts[0] != summary["encounters"]:
            line += (" Cada dominio promedia sólo los encuentros en que fue evaluable, "
                     f"entre {counts[0]} y {counts[-1]}.")
        return line
    line = (f"Orange: this resident's average across {summary['encounters']} confirmed "
            f"encounters.")
    if counts and counts[0] != summary["encounters"]:
        line += (" Each domain averages only the encounters where it was assessable, "
                 f"between {counts[0]} and {counts[-1]}.")
    return line


def table(summary, language="en"):
    """Rows for a screen: domain, mean, how many encounters, last movement."""
    spanish = language == "es"
    rows = []
    for domain in DOMAIN_IDS:
        row = summary["domains"][domain]
        if row["mean"] is None:
            value = "—"
            note = ("Sin encuentro en que fuera evaluable" if spanish
                    else "No encounter where it was assessable")
        else:
            value = f"{row['mean']:.2f} / {MAX_DOMAIN_SCORE}"
            note = (f"{row['encounters']} encuentro(s)" if spanish
                    else f"{row['encounters']} encounter(s)")
            if row["change"]:
                arrow = "↑" if row["change"] > 0 else "↓"
                note += f" · {arrow} {row['change']:+d} " + ("respecto del anterior" if spanish
                                                             else "on the previous one")
            elif row["change"] == 0:
                note += " · " + ("sin cambio respecto del anterior" if spanish
                                 else "unchanged on the previous one")
        rows.append({
            "domain_id": domain,
            "title": row["title_es"] if spanish else row["title"],
            "mean_label": value,
            "note": note,
            "encounters": row["encounters"],
        })
    return rows
