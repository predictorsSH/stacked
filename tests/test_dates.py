from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from stacked.core.config import TIMEZONE
from stacked.core.dates import day_bounds, resolve_target_date

TZ = ZoneInfo(TIMEZONE)


def test_resolve_target_as_is_when_given():
    assert resolve_target_date(date(2026, 11, 9)) == date(2026, 11, 9)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        # 기본 동작: 한국 11/14 오후 → 5일 전
        (datetime(2026, 11, 14, 14, 0, tzinfo=TZ), date(2026, 11, 9)),
        # 경계: UTC로는 13일이지만 한국은 이미 14일 아침
        (datetime(2026, 11, 13, 23, 30, tzinfo=UTC), date(2026, 11, 9)),
        # 경계: 한국 13일 23:59 → 아직 13일
        (datetime(2026, 11, 13, 14, 59, tzinfo=UTC), date(2026, 11, 8)),
    ],
    ids=["KST 14", "UTC 13/KST 14", "UTC 13/KST 13"],
)
def test_now(now, expected):
    assert resolve_target_date(now=now, maturity_days=5) == expected


def test_no_timezone_error():
    with pytest.raises(ValueError):
        resolve_target_date(now=datetime(2026, 11, 14, 14, 0))


def test_returns_midnight_timestamps():
    start, end = day_bounds(date(2026, 11, 9))
    assert start == 1794150000
    assert end == 1794236400
