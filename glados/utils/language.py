from typing import Tuple

# Very naive language detection between English and Ukrainian using character sets
# For production use fastText or langid.py (small) or CLD3.

UKR_CHARS = set("іїєґІЇЄҐ".lower())


def detect_language(text: str) -> str:
    t = text.lower()
    if any(c in UKR_CHARS for c in t):
        return "uk"
    # If Cyrillic letters present but not the special Ukrainian ones, still treat as 'uk' for simplicity
    if any('а' <= c <= 'я' for c in t):
        return "uk"
    return "en"


def normalize_item_query(text: str) -> Tuple[str, str]:
    lang = detect_language(text)
    return text.strip(), lang
