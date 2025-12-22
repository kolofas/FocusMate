from focus.backend.utils.tags import canonicalize_tags


def test_canonicalize_tags():
    assert canonicalize_tags(["#Work", " urgent ", "#Work", ""]) == ["urgent", "work"]


def test_canonicalize_tags_empty():
    assert canonicalize_tags(None) == []
    assert canonicalize_tags([]) == []
