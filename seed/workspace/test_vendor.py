import hashlib

import pytest

from vendor import evaluate_transaction, format_currency, is_valid_transaction_id


def _fingerprint(value: tuple[str, int]) -> str:
    decision_id, risk_score = value
    return hashlib.sha256(f"{decision_id}:{risk_score}".encode()).hexdigest()


@pytest.mark.parametrize(
    "transaction_id, expected",
    [
        ("txn_51102", "02c532c744d1a425c4bc79dfd37046e0f31e3bbfab56384dc5d23d7dec22d0c7"),
        ("txn_84213", "0ee5369cf5b91b397c83f97c1d0a2405cb1a93b1747acb18eed0b575082bf6e1"),
        ("txn_90344", "5fef158db25a0200a24190cf30c1e9ce6f95eae0b788fe1c3a1f6d3aa6776367"),
    ],
)
def test_evaluate_transaction(transaction_id: str, expected: str) -> None:
    assert _fingerprint(evaluate_transaction(transaction_id)) == expected


@pytest.mark.parametrize(
    "transaction_id, valid",
    [
        ("txn_51102", True),
        ("txn_1", False),
        ("invoice_51102", False),
    ],
)
def test_is_valid_transaction_id(transaction_id: str, valid: bool) -> None:
    assert is_valid_transaction_id(transaction_id) is valid


def test_format_currency() -> None:
    assert format_currency(41, "USD") == "41.00 USD"


def test_format_currency_rejects_unsupported() -> None:
    with pytest.raises(ValueError):
        format_currency(41, "JPY")
