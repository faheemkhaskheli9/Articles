"""Script-aware normalization and number extraction for Sindhi, Urdu, Roman Sindhi/Urdu and English.

Everything here is deterministic and uses only the standard library.
"""

from __future__ import annotations

import re
import unicodedata

# Arabic-Indic (U+0660..U+0669) and Extended Arabic-Indic (U+06F0..U+06F9) digits -> ASCII.
# Urdu and Sindhi use the Extended range; Arabic text uses the first range.
_DIGIT_MAP = {0x0660 + i: str(i) for i in range(10)} | {0x06F0 + i: str(i) for i in range(10)}

# Letters that look the same to a reader but have different code points.
_LETTER_MAP = {
    "ك": "ک", "ڪ": "ک",            # Arabic kaf, Sindhi swash kaf -> Urdu kaf
    "ي": "ی", "ى": "ی", "ې": "ی",  # yeh variants
    "ہ": "ه", "ھ": "ه", "ۀ": "ه",  # heh variants (Urdu gol heh, do-chashmi heh)
    "ۃ": "ه", "ة": "ه",
    "ڙ": "ڑ",                       # Sindhi rreh -> Urdu rreh (same sound)
    "أ": "ا", "إ": "ا", "آ": "ا",
    "٬": "", "،": " ",              # Arabic thousands separator / Arabic comma
    "٫": ".",                       # Arabic decimal separator
    "ـ": "",                   # tatweel (kashida)
    "‌": "", "‍": "",     # ZWNJ / ZWJ
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-",
}
_TRANSLATE = str.maketrans({**{chr(k): v for k, v in _DIGIT_MAP.items()}, **_LETTER_MAP})
_TRANSLATE_NO_DIGITS = str.maketrans(_LETTER_MAP)
_DIACRITICS = re.compile(r"[ً-ٰٟ]")  # harakat, superscript alef


def normalize(text: str, script_digits: bool = True) -> str:
    """Return a comparison form: NFKC, ASCII digits, unified letters, no diacritics, casefolded.

    script_digits=False keeps Arabic-script digits as they are (used only for the ablation).
    """
    table = _TRANSLATE if script_digits else _TRANSLATE_NO_DIGITS
    text = unicodedata.normalize("NFKC", text).translate(table)
    text = _DIACRITICS.sub("", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


# --- number words -----------------------------------------------------------------------------
# Units count as numbers on their own only when they are unambiguous. Short Roman words such as
# "do" (2) or "no" (9) are also everyday English, so they count only before a multiplier.
_UNITS = {
    # English
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20, "fifty": 50,
    # Urdu
    "ایک": 1, "دو": 2, "تین": 3, "چار": 4, "پانچ": 5, "چھ": 6, "سات": 7, "آٹھ": 8,
    "دس": 10, "پندرہ": 15, "بیس": 20, "پچاس": 50,
    # Sindhi
    "هڪ": 1, "ٻه": 2, "ٽي": 3, "پنج": 5, "ڇهه": 6, "ست": 7, "اٺ": 8, "ڏهه": 10, "پندرهن": 15, "ويهه": 20,
    "پنجاهه": 50,
    # Roman Urdu / Roman Sindhi
    "ek": 1, "hik": 1, "hikk": 1, "teen": 3, "tin": 3, "char": 4, "chaar": 4, "panch": 5,
    "paanch": 5, "panj": 5, "chhe": 6, "chhah": 6, "saat": 7, "sat": 7, "aath": 8, "ath": 8,
    "nau": 9, "das": 10, "dah": 10, "daha": 10, "pandrah": 15, "pandrahan": 15, "bees": 20, "veeh": 20, "pachas": 50,
    "panjah": 50,
}
_AMBIGUOUS_UNITS = {"do": 2, "ba": 2, "bah": 2, "tey": 3, "te": 3, "no": 9, "نو": 9}
_MULTIPLIERS = {
    "hundred": 100, "sau": 100, "so": 100, "سو": 100, "سؤ": 100,
    "thousand": 1_000, "hazar": 1_000, "hazaar": 1_000, "hajar": 1_000, "هزار": 1_000,
    "lakh": 100_000, "lac": 100_000, "لاکھ": 100_000, "لک": 100_000,
    "crore": 10_000_000, "karor": 10_000_000, "kror": 10_000_000, "کروڑ": 10_000_000,
}

# Normalize lexicon keys with the same function used on user text.
UNITS = {normalize(k): v for k, v in _UNITS.items()}
AMBIGUOUS_UNITS = {normalize(k): v for k, v in _AMBIGUOUS_UNITS.items()}
MULTIPLIERS = {normalize(k): v for k, v in _MULTIPLIERS.items()}

ID_PATTERN = re.compile(r"\b[^\W\d_]+-\d+\b", re.UNICODE)
_TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?|[^\W\d_]+", re.UNICODE)


def _parse_digits(token: str) -> float | None:
    cleaned = token.replace(",", "")  # handles 1,500 and South Asian grouping 1,50,000
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_numbers(text: str, script_digits: bool = True, words: bool = True) -> set[int]:
    """Every integer the user plausibly wrote, from digits in any script and from number words.

    Compound phrases are summed while the multiplier falls: "two lakh fifty thousand" -> 250000.

    >>> sorted(extract_numbers("منهنجي A-100 مان ۱۵۰۰ رپيا"))
    [1500]
    >>> sorted(extract_numbers("panj hazar bhejo"))
    [5000]
    >>> sorted(extract_numbers("ٻه لک پنجاهه هزار"))
    [250000]
    >>> sorted(extract_numbers("one thousand five hundred and 2 seats"))
    [2, 1500]
    >>> sorted(extract_numbers("۱۵۰۰ panj hazar", script_digits=False, words=False))
    []
    """
    # Identifiers such as A-100 or KESC-778812 are not amounts; drop them first.
    norm = normalize(text, script_digits=script_digits)
    toks = [t for t in _TOKEN.findall(ID_PATTERN.sub(" ", norm)) if t.isascii() or not t[0].isdigit()]
    units = (UNITS | AMBIGUOUS_UNITS) if words else {}
    found: set[int] = set()
    total, last_mult = 0, None
    i = 0
    while i < len(toks):
        tok = toks[i]
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        value = _parse_digits(tok) if tok[0].isdigit() else units.get(tok)
        if words and value is not None and nxt in MULTIPLIERS:
            mult = MULTIPLIERS[nxt]
            if last_mult is not None and mult >= last_mult:   # a new number starts
                found.add(round(total))
                total = 0
            total += value * mult
            last_mult = mult
            i += 2
            continue
        if last_mult is not None and tok not in {"and", "aur", "اور", "۽", "ain"}:
            found.add(round(total))
            total, last_mult = 0, None
        if tok[0].isdigit() and value is not None and value == int(value):
            found.add(int(value))
        elif words and tok in UNITS:
            found.add(UNITS[tok])
        elif words and tok in MULTIPLIERS:  # a bare "hazar" means 1000
            found.add(MULTIPLIERS[tok])
        i += 1
    if last_mult is not None:
        found.add(round(total))
    return found


def tokens(text: str) -> list[str]:
    """Normalized word tokens, keeping IDs such as a-100 or kesc-778812 intact."""
    # U+06FE (۾, Sindhi "in") is a symbol, not a letter, so \w alone would drop it.
    return re.findall(r"\w+(?:-\w+)*|\u06FE", normalize(text), flags=re.UNICODE)
