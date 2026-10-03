import re

_PHONE_CLEAN = re.compile(r"[\s\-()]")


def normalize_phone(value: str) -> str:
    """Привести телефон к формату +7XXXXXXXXXX."""
    cleaned = _PHONE_CLEAN.sub("", value)
    if cleaned.startswith("8"):
        cleaned = "+7" + cleaned[1:]
    elif not cleaned.startswith("+7") and len(cleaned) == 10:
        # 9781234567 → +79781234567
        cleaned = "+7" + cleaned
    return cleaned
