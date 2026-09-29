"""What the stores' histories promise, written into the database where the rows allow it (cycle 10).

I-F06. Rubric proposals and reviews, progress drafts, the photos an encounter showed and the
image budget ledger number their rows: the highest so far plus one, taken inside the store's
write lock. The numbers have always been right; nothing in the database said so. A unique
index now does.

I-F19. One current observation per encounter and objective was already a unique index, created
with the tables: a database holding an earlier duplicate could not open its progress store at
all, and every progress page said "temporarily unavailable".

Both now go through ``enforce``: a database that already repeats a key is not refused. Its store
opens as before without that one index, the server log names the table, and
``python3 check_database.py --integrity`` lists the repeats for a person to resolve. The writers
never relied on these indexes to stay correct (they check inside the write lock), so a missing
index takes nothing away.

I-F20. ``decode`` reads a JSON column of one row: a corrupt value no longer takes the whole page
down, the row says it could not be read, and the log names the row, never its content.
"""
import json
import logging

_LOG = logging.getLogger(__name__)

#: index name -> (table, columns that have to be unique together, rows it applies to).
UNIQUE_KEYS = {
    "mrs_rubric_proposals_sequence_unique": ("mrs_rubric_proposals", ("attempt_id", "sequence"), None),
    "mrs_rubric_reviews_sequence_unique": ("mrs_rubric_reviews", ("attempt_id", "sequence"), None),
    "mrs_progress_drafts_sequence_unique": ("mrs_progress_drafts", ("attempt_id", "objective_id", "sequence"),
                                            None),
    "mrs_image_displays_sequence_unique": ("mrs_image_displays", ("attempt_id", "sequence"), None),
    "mrs_image_ledger_sequence_unique": ("mrs_image_ledger", ("seq",), None),
    # The two that existed before cycle 10, under their original names.
    "mrs_progress_current_observation": ("mrs_progress_observations", ("attempt_id", "objective_id"),
                                         "voided_at IS NULL"),
    "mrs_active_resident_attempt": ("mrs_attempts", ("user_id",), "status = 'active' AND is_sandbox = 0"),
}


def repeats(execute, connection, index):
    """The key combinations written more than once, with how many times."""
    table, columns, where = UNIQUE_KEYS[index]
    keys = ", ".join(columns)
    rows = execute(connection, f"""SELECT {keys}, COUNT(*) AS copies FROM {table}
        {'WHERE ' + where if where else ''} GROUP BY {keys} HAVING COUNT(*) > 1 ORDER BY {keys}""").fetchall()
    return [{**{column: row[column] for column in columns}, "copies": int(row["copies"])} for row in rows or []]


def enforce(execute, connection, index):
    """Create the unique index unless earlier rows already repeat its key. Returns the repeats."""
    found = repeats(execute, connection, index)
    if found:
        _LOG.warning("%s holds %d repeated key(s); its unique index %s was not created. "
                     "Run check_database.py --integrity.", UNIQUE_KEYS[index][0], len(found), index)
        return found
    table, columns, where = UNIQUE_KEYS[index]
    execute(connection, f"CREATE UNIQUE INDEX IF NOT EXISTS {index} ON {table}({', '.join(columns)})"
                        + (f" WHERE {where}" if where else ""))
    return []


def decode(text, default, *, table, row_id, column):
    """One row's JSON column, or ``(default, False)`` when it cannot be read. Returns (value, readable)."""
    if text is None or text == "":
        return default, True
    try:
        return json.loads(text), True
    except (TypeError, ValueError):
        _LOG.warning("Unreadable %s.%s in row %s; shown as unreadable.", table, column, row_id)
        return default, False
