from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from stacked.core.config import MATURITY_DAYS, TIMEZONE

TZ = ZoneInfo(TIMEZONE)
SECONDS_PER_DAY = 86400


def resolve_target_date(
    target: date | None = None, *, now: datetime | None = None, maturity_days: int = MATURITY_DAYS
) -> date:

    if target is not None:
        return target

    if now is None:
        now = datetime.now(TZ)

    elif now.tzinfo is None:
        raise ValueError("now에는 timezone이 있는 datetime을 넣어줘야 한다.")

    today = now.astimezone(TZ).date()
    return today - timedelta(days=maturity_days)


def day_bounds(target: date) -> tuple[int, int]:
    """date를 입력받으면 해당 date의 시작과 끝 timestamp(초 단위)를 출력한다."""

    target_datetime = datetime.combine(target, time(0), tzinfo=TZ)
    target_stamp = int(target_datetime.timestamp())

    return target_stamp, target_stamp + SECONDS_PER_DAY
