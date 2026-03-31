from focus.backend.services.telegram.commands.edit import _parse_edit_args


def test_parse_edit_args_with_multiword_title():
    task_id, title = _parse_edit_args(["12", "New", "task", "title"])
    assert task_id == 12
    assert title == "New task title"


def test_parse_edit_args_requires_id_and_title():
    assert _parse_edit_args([]) == (None, None)
    assert _parse_edit_args(["12"]) == (None, None)
    assert _parse_edit_args(["abc", "Title"]) == (None, None)
