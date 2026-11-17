import pytest

from tool_guard.normalize import extract_numbers, normalize, tokens


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("۱۵۰۰ رپيا", {1500}),                 # Extended Arabic-Indic (Urdu/Sindhi)
        ("١٥٠٠ ريال", {1500}),                  # Arabic-Indic
        ("۳٬۴۵۰ روپے", {3450}),                 # Arabic thousands separator
        ("Rs. 1,50,000", {150000}),             # South Asian digit grouping
        ("پنج هزار", {5000}),                   # Sindhi words
        ("پانچ ہزار", {5000}),                  # Urdu words, different heh
        ("paanch hazar", {5000}),               # Roman Urdu
        ("ٻه لک پنجاهه هزار", {250000}),        # compound
        ("2.5 lakh", {250000}),
        ("pandrah sau", {1500}),
        ("fifteen hundred", {1500}),
        ("one thousand five hundred", {1500}),
        ("two seats", {2}),
    ],
)
def test_extract_numbers(text, expected):
    assert extract_numbers(text) == expected


def test_identifiers_are_not_amounts():
    assert extract_numbers("A-100 se B-200 mein 1500") == {1500}
    assert extract_numbers("KESC-778812 ka bill") == set()


def test_ambiguous_roman_words_count_only_before_a_multiplier():
    assert extract_numbers("bill bhar do") == set()      # "do" = do it, not 2
    assert extract_numbers("do hazar") == {2000}


def test_ablation_switches():
    assert extract_numbers("۱۵۰۰", script_digits=False) == set()
    assert extract_numbers("panj hazar", words=False) == set()


def test_letter_variants_compare_equal():
    assert normalize("ڪروڙ") == normalize("کروڑ")
    assert normalize("ہزار") == normalize("هزار")
    assert normalize("A–100") == "a-100"


def test_tokens_keep_ids_and_sindhi_postposition():
    assert tokens("B-200 اڪائونٽ ۾") == ["b-200", "اکائونٽ", "۾"]
