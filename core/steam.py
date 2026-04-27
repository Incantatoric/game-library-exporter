def parse_steam_paste(raw_text: str) -> list[str]:
    """
    Processes the raw text pasted from the Steam browser console snippet.

    The JavaScript snippet already handles deduplication and alphabetical
    sorting before copying to clipboard. This function only strips blank
    lines and whitespace — it does NOT sort, preserving the order the
    user copied.
    """
    lines = raw_text.splitlines()
    return [line.strip() for line in lines if line.strip()]