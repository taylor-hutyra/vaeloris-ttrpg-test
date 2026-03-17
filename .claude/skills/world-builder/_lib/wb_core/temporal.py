"""Temporal state queries (port of query.ts timeline logic).

Works with parsed entity dicts that have 'frontmatter' containing an optional
'timeline' array.  Each timeline entry is a dict with at least a 'period' key
and arbitrary state-override fields.
"""

from __future__ import annotations

import copy
from typing import Optional

from .period import (
    TimePoint,
    TimePeriod,
    WorldCalendar,
    parse_period,
    is_within_period,
    periods_overlap,
)


def get_timeline(entity: dict, calendar: Optional[WorldCalendar] = None) -> list[dict]:
    """Parse and sort timeline entries by start year.

    Each returned entry has '_parsed_period' injected alongside the original
    fields.
    """
    fm = entity.get("frontmatter", {})
    raw_timeline = fm.get("timeline", [])
    if not raw_timeline:
        return []

    entries: list[dict] = []
    for entry in raw_timeline:
        if not isinstance(entry, dict):
            continue
        period_str = entry.get("period")
        if not period_str:
            continue
        parsed = parse_period(str(period_str), calendar)
        enriched = {**entry, "_parsed_period": parsed}
        entries.append(enriched)

    entries.sort(key=lambda e: e["_parsed_period"].start.year)
    return entries


def get_state_at(
    entity: dict,
    time: TimePoint,
    calendar: Optional[WorldCalendar] = None,
) -> dict:
    """Merge base frontmatter with timeline entries active at *time*.

    Later entries override earlier ones (timeline is sorted by start year).
    Returns a new dict — the original is not mutated.
    """
    fm = entity.get("frontmatter", {})
    state = {k: v for k, v in fm.items() if k != "timeline"}

    timeline = get_timeline(entity, calendar)
    for entry in timeline:
        period: TimePeriod = entry["_parsed_period"]
        if is_within_period(time, period):
            # Merge entry fields (skip internal keys)
            for k, v in entry.items():
                if k in ("period", "_parsed_period"):
                    continue
                state[k] = copy.deepcopy(v)

    return state


def diff_between(
    entity: dict,
    t1: TimePoint,
    t2: TimePoint,
    calendar: Optional[WorldCalendar] = None,
) -> list[dict]:
    """Compute state differences between two points in time.

    Returns a list of {"field": str, "from": value, "to": value} dicts for
    every field that changed.
    """
    state1 = get_state_at(entity, t1, calendar)
    state2 = get_state_at(entity, t2, calendar)

    all_keys = set(state1.keys()) | set(state2.keys())
    # Skip meta keys
    skip = {"path", "wb-type"}

    diffs: list[dict] = []
    for key in sorted(all_keys):
        if key in skip:
            continue
        v1 = state1.get(key)
        v2 = state2.get(key)
        if v1 != v2:
            diffs.append({"field": key, "from": v1, "to": v2})

    return diffs


def get_active_label(
    entity: dict,
    time: TimePoint,
    calendar: Optional[WorldCalendar] = None,
) -> Optional[str]:
    """Return the 'label' field from the latest active timeline entry, or None."""
    timeline = get_timeline(entity, calendar)
    label: Optional[str] = None
    for entry in timeline:
        period: TimePeriod = entry["_parsed_period"]
        if is_within_period(time, period):
            if "label" in entry:
                label = entry["label"]
    return label
