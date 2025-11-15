from app.utils.sql_safety import is_select_only

def test_select_only_allows_simple_select():
    assert is_select_only("SELECT * FROM people") is True

def test_select_only_rejects_insert():
    assert is_select_only("INSERT INTO people VALUES (1)") is False
