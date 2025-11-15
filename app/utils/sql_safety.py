import re

SELECT_ONLY_PATTERN = re.compile(r"^\s*select\b", re.IGNORECASE)

FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create table", "create schema", "attach", "copy", "pragma"
]

def is_select_only(sql: str) -> bool:
    """
    Very basic check: must start with SELECT and not include obvious dangerous keywords.
    """
    if not SELECT_ONLY_PATTERN.match(sql or ""):
        return False

    lowered = sql.lower()
    for kw in FORBIDDEN_KEYWORDS:
        if kw in lowered:
            return False
    return True
