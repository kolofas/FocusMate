from datetime import datetime
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")

def to_utc(dt_local: datetime | None) -> datetime | None:
    if dt_local is None:
        return None
    return dt_local.astimezone(UTC)