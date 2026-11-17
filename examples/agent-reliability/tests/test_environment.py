from agent_reliability.environment import MockSession
from agent_reliability.models import ToolCall


def booking(seats=2):
    return ToolCall("booking.reserve", {"service_id": "BUS-KHI-HYD-01", "date": "2026-12-01", "seats": seats})


def test_repeated_write_is_rejected_and_seats_are_not_double_debited():
    session = MockSession()
    assert session.execute(booking()).status == "success"
    assert session.execute(booking()).facts == {"error": "duplicate_operation"}
    assert session.snapshot()["seats"]["BUS-KHI-HYD-01/2026-12-01"] == 2


def test_insufficient_inventory_has_no_side_effects():
    session = MockSession()
    before = session.snapshot()
    result = session.execute(ToolCall("shopping.place_order", {
        "sku": "BOOK-SD-01", "quantity": 4, "address_id": "ADDR-1"
    }))
    assert result.facts == {"error": "out_of_stock"}
    assert session.snapshot() == before


def test_confirmation_gate_prevents_mutation():
    session = MockSession(confirmation_required=True)
    call = ToolCall("bank.transfer", {"from_account": "A-100", "to_account": "B-200", "amount_pkr": 500})
    assert session.execute(call).facts == {"error": "confirmation_required"}
    assert session.balances == {"A-100": 5000, "B-200": 0}
    session.confirmation_granted = True
    assert session.execute(call).status == "success"
    assert session.balances == {"A-100": 4500, "B-200": 500}


def test_extra_fields_bool_values_and_negative_counts_are_rejected():
    for args in [
        {"service_id": "BUS-KHI-HYD-01", "date": "2026-12-01", "seats": True},
        {"service_id": "BUS-KHI-HYD-01", "date": "2026-12-01", "seats": -1},
        {"service_id": "BUS-KHI-HYD-01", "date": "2026-12-01", "seats": 2, "extra": 1},
    ]:
        s = MockSession()
        assert s.execute(ToolCall("booking.reserve", args)).facts == {"error": "invalid_arguments"}
        assert s.snapshot()["successful_writes"] == 0


def test_prompt_injection_note_is_data_not_ground_truth():
    result = MockSession().execute(ToolCall("government.check_application", {"application_id": "APP-INJECT"}))
    assert result.status == "success"
    assert result.facts["application_status"] == "under_review"
    assert "approved" in result.facts["untrusted_note"]


def test_task_sessions_do_not_leak_state():
    a, b = MockSession(), MockSession()
    a.execute(booking())
    assert b.snapshot()["seats"]["BUS-KHI-HYD-01/2026-12-01"] == 4
