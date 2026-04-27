from core.steam import parse_steam_paste


def test_normal_input():
    raw = "Cyberpunk 2077\nThe Witcher 3\nSlay the Spire"
    result = parse_steam_paste(raw)
    assert result == ["Cyberpunk 2077", "The Witcher 3", "Slay the Spire"]


def test_empty_input():
    assert parse_steam_paste("") == []


def test_whitespace_only():
    assert parse_steam_paste("   \n\n   ") == []


def test_strips_blank_lines():
    raw = "Game A\n\n\nGame B\n"
    result = parse_steam_paste(raw)
    assert result == ["Game A", "Game B"]


def test_strips_leading_trailing_spaces():
    raw = "  Game A  \n  Game B  "
    result = parse_steam_paste(raw)
    assert result == ["Game A", "Game B"]