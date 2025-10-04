# tests/test_planner.py
from datetime import datetime, timezone, timedelta
from focus.backend.database import models
from focus.backend.services.planner import score_task

def _task(title="t", tags=None, status="inbox", deadline=None, created_at=None):
    t = models.Task(
        title=title,
        description="",
        source="manual",
        status=status,
        deadline=deadline,
        tags=tags or [],
    )
    # имитируем поля из БД
    t.created_at = created_at or datetime.now(timezone.utc)
    t.updated_at = t.created_at
    return t

def test_score_urgent_tag():
    t = _task(tags=["urgent"])
    assert score_task(t) >= 30

def test_score_deadline_steps_future():
    now = datetime.now(timezone.utc)
    t1 = _task(deadline=now + timedelta(hours=12))   # ≤1d → +30
    t2 = _task(deadline=now + timedelta(days=2))     # ≤3d → +20
    t3 = _task(deadline=now + timedelta(days=5))     # ≤7d → +10
    t4 = _task(deadline=now + timedelta(days=30))    # >7d → +0
    assert score_task(t1) > score_task(t2) > score_task(t3) > score_task(t4)

def test_score_past_deadline_is_high():
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    t = _task(deadline=past)
    # просрочка даёт +40
    assert score_task(t) >= 40
