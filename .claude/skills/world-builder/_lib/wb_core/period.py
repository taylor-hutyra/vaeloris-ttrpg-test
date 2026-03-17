"""Period/timeline parsing and comparison (port of period.ts).

Supports 6 period formats:
  "500"              point
  "200-500"          range
  "501-"             ongoing (open-ended)
  "SA:200"           era-qualified point
  "SA:200-SA:500"    era-qualified range
  "FA:800-SA:100"    cross-era range
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TimePoint:
    year: int
    era: Optional[str] = None

    def absolute_year(self) -> int:
        """Return the year value (already absolute after parsing)."""
        return self.year


@dataclass(frozen=True)
class TimePeriod:
    start: TimePoint
    end: Optional[TimePoint] = None  # None means ongoing


@dataclass
class Era:
    name: str
    abbreviation: str
    start: int          # absolute year
    end: Optional[int]  # None means ongoing


@dataclass
class WorldCalendar:
    eras: list[Era] = field(default_factory=list)
    year_zero: str = ""  # era abbreviation that contains year 0


_ERA_POINT_RE = re.compile(r"^([A-Za-z]+):(-?\d+)$")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_time_point(point: str, calendar: Optional[WorldCalendar] = None) -> TimePoint:
    """Parse a single time-point string like '500' or 'SA:200'."""
    point = point.strip()
    m = _ERA_POINT_RE.match(point)
    if m:
        era_abbr = m.group(1)
        relative_year = int(m.group(2))
        if calendar:
            abs_year = resolve_era_year(era_abbr, relative_year, calendar)
            return TimePoint(year=abs_year, era=era_abbr)
        # Without a calendar we store the relative year and the era label.
        return TimePoint(year=relative_year, era=era_abbr)

    # Plain integer
    return TimePoint(year=int(point))


def resolve_era_year(era_abbr: str, relative_year: int, calendar: WorldCalendar) -> int:
    """Convert an era-relative year to an absolute year."""
    for era in calendar.eras:
        if era.abbreviation == era_abbr:
            return era.start + relative_year
    raise ValueError(f"Unknown era abbreviation: {era_abbr}")


def _split_range(raw: str, calendar: Optional[WorldCalendar]) -> tuple[str, str]:
    """Split a range string into (start_str, end_str).

    Handles era-qualified ranges by trying every '-' as a potential split
    point so that 'FA:800-SA:100' is correctly split rather than splitting
    on the first '-'.
    """
    # Fast path: ongoing ("501-")
    if raw.endswith("-"):
        return raw[:-1], ""

    # If no colon present, simple split on first '-'
    if ":" not in raw:
        idx = raw.find("-")
        if idx == -1:
            raise ValueError(f"Not a range: {raw}")
        return raw[:idx], raw[idx + 1:]

    # Era-qualified: try each '-' as the split and pick the one where both
    # sides parse successfully.
    candidates: list[tuple[str, str]] = []
    for i, ch in enumerate(raw):
        if ch == "-" and i > 0 and i < len(raw) - 1:
            left, right = raw[:i], raw[i + 1:]
            try:
                parse_time_point(left, calendar)
                parse_time_point(right, calendar)
                candidates.append((left, right))
            except (ValueError, IndexError):
                continue

    # Also check ongoing form with era
    if raw.endswith("-"):
        left = raw[:-1]
        try:
            parse_time_point(left, calendar)
            candidates.append((left, ""))
        except (ValueError, IndexError):
            pass

    if not candidates:
        raise ValueError(f"Unable to parse range: {raw}")

    # Prefer the split that yields valid era-qualified points on both sides
    return candidates[-1]


def parse_period(period: str, calendar: Optional[WorldCalendar] = None) -> TimePeriod:
    """Parse a period string into a TimePeriod."""
    period = period.strip()

    # Ongoing: "501-"
    if period.endswith("-") and not period.endswith("--"):
        start_str = period[:-1]
        return TimePeriod(start=parse_time_point(start_str, calendar), end=None)

    # Check for range (contains '-' that is not just a negative sign)
    has_range_dash = False
    for i, ch in enumerate(period):
        if ch == "-" and i > 0:
            # Make sure this '-' is not part of an era prefix like "SA:-5"
            # A range dash is preceded by a digit
            if period[i - 1].isdigit():
                has_range_dash = True
                break

    if has_range_dash:
        start_str, end_str = _split_range(period, calendar)
        if end_str == "":
            return TimePeriod(start=parse_time_point(start_str, calendar), end=None)
        return TimePeriod(
            start=parse_time_point(start_str, calendar),
            end=parse_time_point(end_str, calendar),
        )

    # Single point
    return TimePeriod(
        start=parse_time_point(period, calendar),
        end=parse_time_point(period, calendar),
    )


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_time_point(point: TimePoint) -> str:
    if point.era:
        return f"{point.era}:{point.year}"
    return str(point.year)


def format_period(period: TimePeriod) -> str:
    if period.end is None:
        return f"{format_time_point(period.start)}-"
    if period.start == period.end:
        return format_time_point(period.start)
    return f"{format_time_point(period.start)}-{format_time_point(period.end)}"


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def _abs(tp: TimePoint) -> int:
    return tp.year


def is_within_period(point: TimePoint, period: TimePeriod) -> bool:
    """Check whether a time-point falls within a period (inclusive)."""
    y = _abs(point)
    if y < _abs(period.start):
        return False
    if period.end is not None and y > _abs(period.end):
        return False
    return True


def periods_overlap(a: TimePeriod, b: TimePeriod) -> bool:
    """Check whether two periods overlap (inclusive bounds)."""
    a_start = _abs(a.start)
    a_end = _abs(a.end) if a.end is not None else float("inf")
    b_start = _abs(b.start)
    b_end = _abs(b.end) if b.end is not None else float("inf")
    return a_start <= b_end and b_start <= a_end
