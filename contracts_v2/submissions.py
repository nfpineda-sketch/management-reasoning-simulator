"""Submission/persistence contract v2 (Phase 1 WP7).

Representational only. It mirrors existing Phase-0 submission-log entries
exactly. It does not capture, persist, retry, recover, execute, or mutate
submissions.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

SCHEMA = "submission_contract_v2"
VERSION = 2


class SubmissionContractError(RuntimeError):
    """Legacy submission data cannot be represented safely."""


class SubmissionContractMismatch(SubmissionContractError):
    """The v2 submission shadow differs from the legacy submission log."""


@dataclass(frozen=True, slots=True)
class SubmissionEntry:
    payload: dict[str, Any]

    @property
    def submission_id(self):
        return self.payload.get("id")

    @property
    def form_id(self):
        return self.payload.get("form_id")

    @property
    def raw_text(self):
        return self.payload.get("raw_text")

    @property
    def entry_point(self):
        return self.payload.get("entry_point")

    @property
    def status(self):
        return self.payload.get("status")

    @property
    def duplicates(self):
        return self.payload.get("duplicates")

    @property
    def retries(self):
        return self.payload.get("retries")

    @property
    def saved_before_run(self):
        return self.payload.get("saved_before_run")

    def legacy_payload(self) -> dict[str, Any]:
        return deepcopy(self.payload)


@dataclass(frozen=True, slots=True)
class SubmissionLog:
    entries: tuple[SubmissionEntry, ...]
    schema: str = SCHEMA
    version: int = VERSION

    def legacy_projection(self) -> list[dict[str, Any]]:
        return [entry.legacy_payload() for entry in self.entries]

    def as_record(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "submission_log": self.legacy_projection(),
        }


def _copy_entries(entries: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    copied = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise SubmissionContractError(
                f"submission entry {index} is not a mapping: {type(entry).__name__}"
            )
        copied.append(deepcopy(dict(entry)))
    return copied


def from_legacy_entries(entries: Iterable[Mapping[str, Any]] | None) -> SubmissionLog:
    copied = _copy_entries(entries or [])
    return SubmissionLog(
        entries=tuple(SubmissionEntry(payload=entry) for entry in copied)
    )


def assert_shadow_equivalent(
    contract: SubmissionLog,
    entries: Iterable[Mapping[str, Any]] | None,
) -> None:
    expected = _copy_entries(entries or [])
    actual = contract.legacy_projection()
    if actual != expected:
        raise SubmissionContractMismatch(
            f"submission log differs: v2={actual!r} legacy={expected!r}"
        )


def shadow_from_legacy_entries(
    entries: Iterable[Mapping[str, Any]] | None,
) -> SubmissionLog:
    contract = from_legacy_entries(entries)
    assert_shadow_equivalent(contract, entries)
    return contract
