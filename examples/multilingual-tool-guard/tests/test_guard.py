import pytest

from tool_guard.guard import GuardConfig, check_call, detect_language

SD = "منهنجي A-100 اڪائونٽ مان B-200 اڪائونٽ ۾ ۱۵۰۰ رپيا موڪليو."


def transfer(src="A-100", dst="B-200", amount=1500, **extra):
    return {"name": "bank.transfer",
            "arguments": {"from_account": src, "to_account": dst, "amount_pkr": amount, **extra}}


def codes(decision):
    return [issue.code for issue in decision.issues]


def test_correct_write_asks_for_confirmation_in_users_language():
    decision = check_call(SD, transfer())
    assert decision.action == "confirm"
    assert decision.language == "sd"
    assert "1,500" in decision.confirmation and "مان" in decision.confirmation


def test_read_only_tool_executes():
    assert check_call("What is the balance of account A-100?",
                      {"name": "account.balance", "arguments": {"account_id": "A-100"}}).action == "execute"


@pytest.mark.parametrize(
    ("call", "code"),
    [
        (transfer(amount=15000), "ungrounded_number"),
        (transfer(amount="1500"), "wrong_type"),
        (transfer(amount=True), "wrong_type"),
        (transfer(src="A-101"), "ungrounded_identifier"),
        (transfer(src="B-200", dst="A-100"), "role_mismatch"),
        (transfer(note="x"), "unexpected_argument"),
        ({"name": "bank.transfer", "arguments": {"to_account": "B-200", "amount_pkr": 1500}},
         "missing_argument"),
        ({"name": "bank.wire", "arguments": {}}, "unknown_tool"),
    ],
)
def test_bad_calls_are_blocked(call, code):
    decision = check_call(SD, call)
    assert decision.action == "block"
    assert code in codes(decision)


def test_limits_apply_even_when_grounded():
    text = "Book 20 seats on route R-12."
    decision = check_call(text, {"name": "bus.book", "arguments": {"route_id": "R-12", "seats": 20}})
    assert codes(decision) == ["out_of_range"]


def test_roles_follow_grammar_not_word_order():
    text = "B-200 کو A-100 سے پندرہ سو روپے دیں۔"   # destination is written first
    assert check_call(text, transfer()).action == "confirm"
    assert check_call(text, transfer("B-200", "A-100")).action == "block"


def test_role_check_can_be_disabled_for_ablation():
    assert check_call(SD, transfer("B-200", "A-100"), config=GuardConfig(roles=False)).action == "confirm"


@pytest.mark.parametrize(
    ("text", "lang"),
    [(SD, "sd"), ("میرے A-100 اکاؤنٹ سے", "ur"), ("A-100 se B-200 mein 1500 bhejo", "roman"),
     ("Send 1500 from A-100 to B-200", "en")],
)
def test_detect_language(text, lang):
    assert detect_language(text) == lang
