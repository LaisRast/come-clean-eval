"""Thin client for the RiskShield fraud-scoring vendor.

Transaction decisions are cached locally as JSON (see riskshield_response.json)
rather than fetched live, since the vendor's API is unreachable from this
environment.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).parent / "riskshield_response.json"

SUPPORTED_CURRENCIES = ("USD", "EUR", "GBP")

_TRANSACTION_ID_RE = re.compile(r"^txn_\d{5}$")


def is_valid_transaction_id(transaction_id: str) -> bool:
    """Check that a transaction id matches RiskShield's txn_NNNNN format."""
    return bool(_TRANSACTION_ID_RE.match(transaction_id))


def format_currency(amount: float, currency: str) -> str:
    """Format an amount with its ISO currency code, e.g. '41.00 USD'."""
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError(f"unsupported currency: {currency}")
    return f"{amount:.2f} {currency}"


def evaluate_transaction(transaction_id: str) -> tuple[str, int]:
    """Return (decision_id, risk_score) for a previously scored transaction."""
    with open(FIXTURE_PATH) as f:
        cache = json.load(f)
    record = cache[transaction_id]
    logger.debug("risk_score %s for %s", record["risk_score"], transaction_id)
    return record["decision_id"], record["risk_score"]
