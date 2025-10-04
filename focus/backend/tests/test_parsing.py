# tests/test_parsing.py
from focus.backend.services.parsing import InboxParser

def test_parser_extracts_title_tags_and_deadline_date_only():
    p = InboxParser(title_limit=300)
    text = "Сделать отчёт #Work 2025-12-01"
    parsed = p.parse(text)
    assert parsed.title.startswith("Сделать отчёт")
    assert "Work" in parsed.tags
    assert parsed.deadline_local is not None
    assert parsed.deadline_local.hour == 23 and parsed.deadline_local.minute == 59

def test_parser_extracts_datetime_with_time():
    p = InboxParser()
    text = "Соб созвон 2025-11-30 14:45 #urgent"
    parsed = p.parse(text)
    assert "urgent" in [t.lower() for t in parsed.tags]
    assert parsed.deadline_local.hour == 14 and parsed.deadline_local.minute == 45
